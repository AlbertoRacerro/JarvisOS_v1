# A5-R2-R1 - Fix Italian ricorda clitic false positives

## Summary

- base commit: `190f13e0ae286765707ce8bb333a23c094ec07e5`
- fixed `ricorda` clitic false positives in memory-write and credential-like save detection
- covered `mi`, `ti`, `si`, `ci`, `vi`, `gli`, and `le` before `ricorda`
- preserved true `ricorda` memory-write and credential-save blocking
- did not broaden Italian detector coverage

## Scope

- files changed:
  - `scripts/router_policy_message_route_smoke.py`
  - `tests/test_router_policy_message_route_smoke.py`
  - `backend/tests/test_dev_local_chat.py`
  - `reports/router_policy/1G-B2-F3-A5-R2-R1/summary.json`
  - `reports/router_policy/1G-B2-F3-A5-R2-R1/summary.md`
- BlueRev/IP-sensitive marker detection added: `false`
- external routing added: `false`
- frontend modified: `false`
- local responder modified: `false`
- prompt contract modified: `false`

## Results

- memory-write `ricorda` examples still block end-to-end
- credential-save `ricorda` examples still block end-to-end
- clitic reminiscence examples execute through the mocked local responder
- A5-R2 existing blocks remain covered

## Residual Risks

- A5-R2-R1 fixes confirmed false positives in ricorda/clitic forms only.
- A5-R2-R1 does not broaden Italian detector coverage.
- `ricordami di salvare questo` remains a possible future false negative.
- Declarative third-person phrases such as `il sistema ricorda che...` may remain conservative false positives.
- Additional paraphrases such as `segnati`, `documenta`, and `metti nel verbale` remain possible future detector work.
- BlueRev/IP-sensitive marker detection remains deferred to A5-R3.
- External routing remains disabled.
