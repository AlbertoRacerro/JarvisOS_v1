# 154c — Privacy fail-closed default

State: **ready**. Combined definition, contract and readiness, authorized by the maintainer's 2026-09-28 pre-155 directive: strategic, proprietary, confidential or credential-bearing information must never reach an external provider unless Jarvis first builds an explicitly permitted derivative. Smallest change inside the accepted 059/059b egress contract; no new authority, provider or egress surface.

## Fresh baseline

059/059b/129 route every external provider call through one server-owned egress spine: exact packet, deterministic S2/S3/S4 floors, approved derivatives or a local sanitizer, provenance of what left and to which provider/model, confirmation and budget. 059 accepts two operating modes: `STRICT_IP` keeps fail-closed handling of unclassified input, and `FAST_DEV` may treat marker-free prompt text as S1.

New settings rows, missing values and unrecognised values all resolve to `FAST_DEV`. The floors are lexical. Proprietary prose without a recognised marker (process topology, design rationale, unreleased architecture) is therefore external-eligible S1 by default as soon as a paid provider is enabled. The 2026-09-28 code map and privacy research both identify this as the one gap between the existing spine and the maintainer's hard constraint. Model judgement is not an acceptable substitute (ConfAIde: 39–57 % contextual disclosure by frontier models).

## Accepted capability

1. The default policy mode is `STRICT_IP` for new settings rows and for missing or unrecognised stored values. An unclassified prompt pauses with `prompt_classification_required` instead of becoming S1. The existing classification/derivative/confirmation path then applies (ask the user, approved derivative, or stay local).
2. `FAST_DEV` remains an explicit operator opt-in through the existing settings API. An existing stored `FAST_DEV` row is not rewritten; the operator machine is switched explicitly.

## Non-goals

- No change to floors, sanitizer, derivative, packet, confirmation, budget or provider code; no new privacy class vocabulary; no cloud route in the Sidecar.

## Required evidence

- Tests: the default settings row is `STRICT_IP`; missing or unrecognised values resolve to `STRICT_IP`; under the default, a marker-free prompt is not external-eligible and exposes no effective prompt. Existing `FAST_DEV` behaviour tests pin `FAST_DEV` explicitly and still pass.
- The operator machine reports `STRICT_IP` after the change.

## Completion

Enabling a paid provider no longer makes unmarked proprietary text cloud-eligible by default. Registry and PR association are reconciled after merge.
