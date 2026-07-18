from pathlib import Path

CONFIRMATION = Path("backend/app/modules/ai/egress_confirmation.py")
MODELS = Path("backend/app/modules/ai/models.py")
FLOW = Path("backend/app/modules/ai/token_flow_service.py")
CONFIRMATION_TEST = Path("backend/tests/test_ai_egress_confirmation.py")
ENDPOINT_TEST = Path("backend/tests/test_ai_task_endpoint.py")

confirmation = CONFIRMATION.read_text(encoding="utf-8")
old_import = """from app.modules.ai.settings import get_ai_settings\n"""
new_import = """from app.modules.ai.settings import get_ai_settings\nfrom app.modules.ai.token_flow_runtime import normalize_finish_reason\n"""
if confirmation.count(old_import) != 1:
    raise SystemExit("unexpected confirmation import anchor")
confirmation = confirmation.replace(old_import, new_import, 1)
old_capture = """    if status == \"success\":\n        proposed_ids, parse_error = _create_proposed_records_from_response(\n"""
new_capture = """    if status == \"success\" and normalize_finish_reason(\n        response.finish_reason, failed=response.error is not None\n    ) != \"length\":\n        proposed_ids, parse_error = _create_proposed_records_from_response(\n"""
if confirmation.count(old_capture) != 1:
    raise SystemExit("unexpected confirmed-ticket capture anchor")
CONFIRMATION.write_text(confirmation.replace(old_capture, new_capture, 1), encoding="utf-8")

models = MODELS.read_text(encoding="utf-8")
old_task_field = '    task_kind: str = "general"\n'
new_task_field = (
    '    task_kind: str = Field(\n'
    '        default="general", pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$"\n'
    '    )\n'
)
if models.count(old_task_field) != 1:
    raise SystemExit("unexpected AITaskRunRequest task_kind field")
MODELS.write_text(models.replace(old_task_field, new_task_field, 1), encoding="utf-8")

flow = FLOW.read_text(encoding="utf-8")
old_task_re = 'TASK_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")\n'
new_task_re = 'TASK_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")\n'
if flow.count(old_task_re) != 1:
    raise SystemExit("unexpected token-flow task regex")
FLOW.write_text(flow.replace(old_task_re, new_task_re, 1), encoding="utf-8")

confirmation_tests = CONFIRMATION_TEST.read_text(encoding="utf-8")
confirmation_case = '''\n\ndef test_length_stopped_confirmed_ticket_skips_record_capture(monkeypatch) -> None:\n    ticket_id = _pending_ticket(monkeypatch)\n    response = _success_response().model_copy(update={"finish_reason": "length"})\n    adapter = _Adapter("deepseek", response=response)\n    import app.modules.ai.egress_confirmation as confirmation\n\n    def fail_capture(**_kwargs):\n        pytest.fail("truncated confirmed output must not create proposed records")\n\n    monkeypatch.setattr(\n        confirmation, "_create_proposed_records_from_response", fail_capture\n    )\n\n    outcome = run_confirmation_ticket(\n        ticket_id, adapters={"deepseek": adapter}\n    ).outcome\n\n    assert outcome.status == "success"\n    assert outcome.response is not None\n    assert outcome.response.finish_reason == "length"\n    assert outcome.proposed_record_ids is None\n    assert outcome.records_parse_error is None\n'''
if "test_length_stopped_confirmed_ticket_skips_record_capture" in confirmation_tests:
    raise SystemExit("confirmation regression test already exists")
CONFIRMATION_TEST.write_text(confirmation_tests + confirmation_case, encoding="utf-8")

endpoint_tests = ENDPOINT_TEST.read_text(encoding="utf-8")
endpoint_cases = '''\n\n@pytest.mark.parametrize("task_kind", ["code-review", "CODE_REVIEW"])\ndef test_task_endpoint_accepts_safe_task_kind_variants(\n    client: TestClient, task_kind: str\n) -> None:\n    response = client.post(\n        "/ai/tasks/run",\n        json={\n            "prompt": "Validate task kind compatibility.",\n            "route_class": "local:fake",\n            "task_kind": task_kind,\n            "max_tokens": 32,\n        },\n    )\n\n    assert response.status_code == 200\n    jobs = _all_ai_jobs()\n    assert len(jobs) == 1\n    assert jobs[0]["task_kind"] == task_kind\n    assert jobs[0]["flow_id"] is not None\n\n\ndef test_task_endpoint_rejects_malformed_task_kind_before_execution(\n    client: TestClient, monkeypatch: pytest.MonkeyPatch\n) -> None:\n    import app.modules.ai.execution as execution\n\n    def fail_execution(**_kwargs):\n        pytest.fail("malformed task_kind must be rejected before execution")\n\n    monkeypatch.setattr(execution, "run_ai_task", fail_execution)\n    response = client.post(\n        "/ai/tasks/run",\n        json={\n            "prompt": "Reject malformed task kind.",\n            "route_class": "local:fake",\n            "task_kind": "bad kind!",\n            "max_tokens": 32,\n        },\n    )\n\n    assert response.status_code == 422\n    assert _all_ai_jobs() == []\n'''
if "test_task_endpoint_accepts_safe_task_kind_variants" in endpoint_tests:
    raise SystemExit("task-kind regression tests already exist")
ENDPOINT_TEST.write_text(endpoint_tests + endpoint_cases, encoding="utf-8")
