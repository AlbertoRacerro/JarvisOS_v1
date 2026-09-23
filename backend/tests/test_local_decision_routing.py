from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.ai.contracts import RoutingDecision
from app.modules.ai.execution import AiTaskOutcome
from app.modules.ai.provider_registry import load_default_provider_registry
from app.modules.local_ai import local_router
from app.modules.local_ai.decision_contracts import (
    DecisionContractError,
    DecisionOutputSpec,
    DecisionRequest,
    DecisionResult,
)
from app.modules.local_ai.decision_service import GlinerDecisionModel, LocalCandidate, RuleDecisionModel
from app.modules.local_ai.local_router import local_candidates, run_local_selected_task
from app.modules.local_ai.resource_arbiter import InProcessResourceArbiter, ResourceCapacityError
from app.modules.local_ai.resource_contracts import (
    CpuState,
    LoadedModelState,
    MemoryState,
    ResourceAmounts,
    ResourceLeaseError,
    ResourceReservationRequest,
    RuntimeResourceSnapshot,
)
from app.modules.local_ai.runtime.resource_observation import parse_nvidia_smi
from app.modules.local_ai_eval.decision_routing import score_rule_ranker

NOW = datetime.now(UTC)


def observed(*, cores: int | None = 1, loaded: tuple[str, ...] = ()) -> RuntimeResourceSnapshot:
    return RuntimeResourceSnapshot(
        generation=0, observed_at=datetime.now(UTC),
        cpu=CpuState(logical_cores=cores, utilization=0.0 if cores is not None else None), memory=MemoryState(available_bytes=1024),
        loaded_models=tuple(LoadedModelState(name=name) for name in loaded),
    )


def reservation(generation: int, *, model: str = "qwen3:8b") -> ResourceReservationRequest:
    now = datetime.now(UTC)
    return ResourceReservationRequest(
        request_id="r-1", owner_kind="inference_envelope", owner_id="env-1", correlation_id="d-1",
        resources=ResourceAmounts(cpu_cores=1, model_name=model), snapshot_generation=generation,
        requested_at=now, deadline_at=now + timedelta(seconds=30), max_hold_seconds=20,
    )


def decision_request(snapshot: RuntimeResourceSnapshot, ids: tuple[str, ...]) -> DecisionRequest:
    now = datetime.now(UTC)
    return DecisionRequest(
        decision_id="d-1", decision_type="local_model.select", candidate_set=ids,
        output_specs=(DecisionOutputSpec(name="fit", kind="score"),),
        constraints={"context_tokens": 100}, resource_snapshot=snapshot,
        requested_at=now, deadline_at=now + timedelta(seconds=30),
    )


def test_unknown_capacity_is_not_zero_or_assumed_available() -> None:
    arbiter = InProcessResourceArbiter(lambda: observed(cores=None, loaded=("qwen3:8b",)))
    snapshot = arbiter.snapshot()
    assert snapshot.cpu.logical_cores is None
    with pytest.raises(ResourceCapacityError):
        arbiter.reserve(reservation(snapshot.generation))
    no_util = observed(loaded=("qwen3:8b",)).model_copy(update={"cpu": CpuState(logical_cores=1)})
    arbiter = InProcessResourceArbiter(lambda: no_util)
    with pytest.raises(ResourceCapacityError):
        arbiter.reserve(reservation(arbiter.snapshot().generation))


def test_stale_generation_and_competing_reservations() -> None:
    arbiter = InProcessResourceArbiter(lambda: observed(loaded=("qwen3:8b",)))
    stale = arbiter.snapshot().generation
    lease = arbiter.reserve(reservation(stale))
    with pytest.raises(ResourceLeaseError, match="generation") as exc:
        arbiter.reserve(reservation(stale))
    assert exc.value.code == "stale_snapshot"
    arbiter.end(lease.lease_id, expected_version=1, reason="completed")

    generation = arbiter.snapshot().generation
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(arbiter.reserve, reservation(generation)) for _ in range(8)]
    results = [future.exception() if future.exception() else future.result() for future in futures]
    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert all(isinstance(result, ResourceLeaseError) for result in results if isinstance(result, Exception))


def test_observation_change_and_gpu_parser() -> None:
    current = [observed()]
    arbiter = InProcessResourceArbiter(lambda: current[0])
    first = arbiter.snapshot()
    assert arbiter.snapshot().generation == first.generation
    current[0] = observed(cores=2)
    assert arbiter.snapshot().generation == first.generation + 1
    with pytest.raises(ResourceLeaseError) as stale:
        arbiter.reserve(reservation(first.generation))
    assert stale.value.code == "stale_snapshot"
    parsed = parse_nvidia_smi("0, RTX 5070, 12288, 1024\ninvalid\n1, Bad, 10, 20")
    assert len(parsed) == 1 and parsed[0].vram_total_bytes == 12288 * 1024**2


def test_rule_ranking_abstention_and_result_gate() -> None:
    candidate = LocalCandidate("local:fast", "qwen3:8b", 8192, frozenset({"fast"}))
    request = decision_request(observed(loaded=("qwen3:8b",)), (candidate.candidate_id,))
    result = RuleDecisionModel().decide(request, (candidate,))
    assert result.selected_candidate == "local:fast"
    no_fit = decision_request(observed(), (candidate.candidate_id,))
    assert RuleDecisionModel().decide(no_fit, (candidate,)).reason_code == "no_candidate_fits"
    with pytest.raises(ValidationError):
        DecisionResult(decision_id="d-1", outcome="decided", selected_candidate="local:fast", model_ref="x", reason_code="x", decided_at=NOW,
                       outputs=({"name": "fit", "kind": "score", "value": 1.1},))  # type: ignore[arg-type]
    class InvalidModel:
        def decide(self, request: DecisionRequest, candidates: tuple[LocalCandidate, ...]) -> DecisionResult:
            return DecisionResult(decision_id=request.decision_id, outcome="decided", selected_candidate="external:cheap",
                                  outputs=(), model_ref="bad", reason_code="ranked", decided_at=NOW)
    arbiter = InProcessResourceArbiter(lambda: observed(loaded=("qwen3:8b",)))
    with pytest.raises(DecisionContractError):
        run_local_selected_task(user_prompt="x", task_kind="general", owner_id="env-1", arbiter=arbiter,
                                candidates=(candidate,), decision_model=InvalidModel())
    admitted = run_local_selected_task(user_prompt="x", task_kind="general", owner_id="env-1", arbiter=arbiter,
                                       candidates=(candidate,), context_tokens=8192, decision_model=InvalidModel())
    assert admitted.status == "abstained" and admitted.attempts[0].decision.reason_code == "no_candidate_fits"


def test_optional_classifier_output_stays_inside_typed_candidate_gate() -> None:
    class LocalClassifier:
        def __init__(self, label: str, confidence: float) -> None:
            self.label, self.confidence = label, confidence

        def classify_text(self, task: str, schema: dict[str, list[str]], *, include_confidence: bool) -> dict[str, object]:
            assert include_confidence and task == "code"
            assert schema == {"local_model": ["local:fast"]}
            return {"local_model": {"label": self.label, "confidence": self.confidence}}

    candidate = LocalCandidate("local:fast", "qwen3:8b", 8192, frozenset({"fast"}))
    request = decision_request(observed(loaded=("qwen3:8b",)), (candidate.candidate_id,))
    request = request.model_copy(update={"constraints": {**request.constraints, "task_text": "code"}})
    assert GlinerDecisionModel(LocalClassifier("local:fast", 0.9), "abc").decide(request, (candidate,)).selected_candidate == "local:fast"
    assert GlinerDecisionModel(LocalClassifier("external:cheap", 0.99), "abc").decide(request, (candidate,)).outcome == "abstained"
    assert GlinerDecisionModel(LocalClassifier("local:fast", 0.4), "abc").decide(request, (candidate,)).outcome == "abstained"


def test_typed_decision_corpus_scorer() -> None:
    metrics = score_rule_ranker()
    assert (metrics.count, metrics.correct, metrics.abstentions) == (5, 5, 3)
    assert sum(bucket.count for bucket in metrics.buckets) == 2


def test_fallback_after_provider_failure_and_local_only_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = load_default_provider_registry()
    assert len({candidate.model_name for candidate in local_candidates(registry)}) == len(local_candidates(registry))
    candidates = (
        LocalCandidate("local:fast", "qwen3:8b", 8192, frozenset({"fast"})),
        LocalCandidate("local:general", "gemma4:12b-it-qat", 8192, frozenset({"general"})),
    )
    arbiter = InProcessResourceArbiter(lambda: observed(loaded=("qwen3:8b", "gemma4:12b-it-qat")))
    seen: list[str] = []
    def execute(**kwargs: object) -> AiTaskOutcome:
        route = kwargs["route_class"]
        assert isinstance(route, str)
        bindings = kwargs["bindings"]
        assert isinstance(bindings, dict)
        binding = bindings[route]
        assert binding.execution_class == "local_compute" and not binding.requires_network
        seen.append(route)
        return AiTaskOutcome("provider_error" if len(seen) == 1 else "success", f"job-{len(seen)}", route, RoutingDecision())
    monkeypatch.setattr(local_router, "run_ai_task", execute)
    outcome = run_local_selected_task(user_prompt="x", task_kind="general", owner_id="env-1", arbiter=arbiter,
                                      registry=registry, candidates=candidates)
    assert outcome.status == "success" and seen == ["local:fast", "local:general"]
    assert len(outcome.attempts) == 2 and all(attempt.lease_id and attempt.ledger_id for attempt in outcome.attempts)
    assert arbiter.snapshot().active_lease_ids == ()
    external = LocalCandidate("external:cheap", "deepseek-v4-pro", 8192, frozenset())
    with pytest.raises(ValueError, match="local-only"):
        run_local_selected_task(user_prompt="x", task_kind="general", owner_id="env-1", arbiter=arbiter,
                                candidates=(external,))
