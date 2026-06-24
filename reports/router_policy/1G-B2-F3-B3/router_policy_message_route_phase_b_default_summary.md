# 1G-B2-F3-B3 - Default Phase B hints in message route smoke

Start HEAD: `6a39a42d6d990cc4534b8fe47ab4af5ce3f81baa`

## Default Behavior

B3 changes only the message-route smoke default:

- library default: `use_phase_b_hints=True`
- CLI default: Phase B hints enabled
- opt-out: `--no-phase-b-hints`
- backward-compatible alias: `--use-phase-b-hints`
- conflicting flags: rejected by argparse

No stdout compatibility warning was added; CLI stdout remains machine-readable
safe JSON.

## Integration Order

```text
A5 builder completes:
  policy overlay
  operational overlay
  hard gate check
  assume_public_simple safe path only if no gate
then:
  apply B1 hint bridge if use_phase_b_hints=True
then:
  structural validation
  RouterPolicy decision
  semantic validator
  A3 safe-local guard
```

B1 is not called inside the builder and is not applied twice.

## Results

- default-on library path applies B1;
- explicit `use_phase_b_hints=False` disables B1;
- CLI default applies B1 exactly once;
- `--use-phase-b-hints` applies B1 exactly once;
- `--no-phase-b-hints` applies B1 zero times;
- `--assume-public-simple` remains required for benign local execution;
- `--run-local` remains required for real local responder construction;
- `--run-local` alone does not execute;
- hard-gate and operational-intent inputs do not execute;
- source/current-info remains conservative;
- scientific-depth remains subject to A3 safe-local guard;
- B1 failure fails closed with `phase_b_hint_bridge_failed`;
- CLI output remains redacted and does not include raw `input_obj`.

## Checks

- `python -m unittest tests.test_router_policy_message_route_smoke`
- `python -m unittest tests.test_router_policy_hint_bridge_probe`
- `python -m unittest tests.test_router_policy_local_responder`
- `python -m unittest tests.test_router_policy_local_route_probe`
- `python -m unittest tests.test_router_policy_decision_probe`
- `python -m unittest tests.test_router_policy_semantic_validator`
- `python -m unittest discover -s tests`
- `git diff --check`
- focused runtime grep

## Runtime Boundary

Real model calls during tests: false.

Added runtime behavior:

- external provider: false
- tool/MCP/browser/terminal: false
- memory/retrieval: false
- file-write runtime: false
- backend/frontend/DB: false
- workers/hooks: false
- BlueRev behavior: false

## Known Residual Risks

- Phase B hints are default-on in smoke only.
- Phase B hints are advisory and non-authoritative.
- A5 remains smoke-only and not a production Phase A/B normalizer.
- `--assume-public-simple` is still required for benign local execution.
- `--run-local` is still required for real local responder construction.
- The A5 Phase B stub remains a smoke placeholder, not live Qwen/Phase B
  semantic output.
- B3 does not approve live Qwen/Gemma/Ollama classification.
- B3 does not approve production chat or removal of `--assume-public-simple`.

Recommended next milestone:

```text
1G-B2-F3-B3-R - Default Phase B Hint Bridge Audit
```
