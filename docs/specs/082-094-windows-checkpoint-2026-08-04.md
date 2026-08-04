# Specs 082/094 Windows checkpoint — 2026-08-04

## Decision

The final operator-visible Windows checkpoint required by spec 082 is accepted.
Spec 094 is already merged through PR #221, and the accepted run proves that the
persisted Scaleway credential can be used after a same-user backend restart through
the normal `run_ai_task` / 059b execution spine. Spec 082 may therefore be
reconciled from `blocked` to `merged`.

This record authorizes only the next queue transition: a fresh definition-only
re-derivation of spec 070 UI-FOUNDATION-1 from current `master`. It does not
provide 070 implementation or readiness authority.

## Pinned environment

- repository: `AlbertoRacerro/JarvisOS_v1`;
- exact tested `master`: `e5c939c3ab62d4904c65aa0ebdec8dbb496f7369`;
- accepted evidence package ID: `082-094-20260804T174450Z`;
- operator platform: Windows PowerShell under the same Windows user that saved the credential;
- JarvisOS data root: `C:\JarvisOS`;
- process environment contained no `SCALEWAY_API_KEY`, `SCALEWAY_BASE_URL`, or
  `AI_ROUTE_SCALEWAY_MODEL` override;
- the tested worktree was clean and detached at the exact commit above;
- the original divergent working repository was not modified.

The local evidence package remains under the operator-owned data root. It is not
committed because it contains local operational records that are unnecessary for
repository authority. No credential, ciphertext, key fragment, response body
beyond the bounded acceptance token, or local user-profile path is copied here.

## Credential and restart proof

Before dispatch, the same-user restarted backend reported the persisted Scaleway
credential as:

- effective source: `secure_persisted`;
- persisted state: `usable`;
- storage mode: `secure_persisted`;
- no masked preview or key-derived value.

The key was not re-entered and was not supplied through the process environment.

## Normal-spine provider proof

The accepted run used exactly one task request and, when required by 059b, exactly
one confirmation of the ticket returned by that request:

- route: `external:scaleway`;
- provider: `scaleway`;
- registry-bound model: `gemma-4-26b-a4b-it`;
- prompt: `Reply with the word OK.`;
- requested output ceiling: 256 tokens;
- project context: excluded;
- caller context blocks: none;
- fallback index: zero;
- second task submission: none;
- terminal provider outcome: success;
- normalized response: `OK`.

The 256-token ceiling is the existing conservative JarvisOS route maximum, not a
claim that 256 tokens were consumed. The model terminated after the bounded `OK`
response. An earlier non-accepting 8-token probe is not used as acceptance
evidence.

## Relational and accounting evidence

Offline extraction from the same SQLite state validated the linked normal-spine
records without another provider call:

- one canonical flow and its initial confirmation-required job;
- one terminal provider job produced by the returned 059b ticket;
- one exact egress packet and decision;
- one consumed ticket and finalized reservation;
- one provider attempt with no fallback;
- adapter invocation and external dispatch evidence;
- provider/model identity and output ceiling;
- normalized usage source, token fields and accounted provider cost;
- terminal response identity and flow completion.

The primary accepted checkpoint script completed the provider call but stopped in
its evidence-extraction wrapper. The corrected offline salvage read the already
persisted evidence, started no backend, submitted no task, confirmed no ticket,
made no network request and returned:

```text
SALVAGE_ACCEPTED: PROVIDER_SUCCESS
SETTINGS_RESTORED
LEAK_NOT_FOUND
```

Acceptance therefore rests on the same single successful provider call, not on a
replacement call.

## Restoration and leak scan

The temporary paid-provider settings were restored to their saved values. The
only textual comparison discrepancy encountered during manual verification was
`2` versus `2.0` for the same numeric monthly budget value; no semantic settings
difference remained.

The anti-leak scan resolved the real persisted key only inside the same-user
protected process and checked the full value plus bounded fragments across:

- HTTP requests and responses retained for the checkpoint;
- backend stdout and stderr;
- application logs and events;
- every logical SQLite cell, including WAL/SHM-backed state;
- the JarvisOS data root, artifacts and checkpoint evidence;
- repository and safe worktree files, excluding generated caches;
- temporary checkpoint files.

The terminal result was `LEAK_NOT_FOUND`. The repository record deliberately
contains no key, fragment, digest, length, ciphertext or masked preview.

## Boundary

This reconciliation changes documentation only. It performs no provider call,
credential mutation or deletion, runtime change, test change, dependency change,
schema or migration, provider configuration change, frontend work, workflow
change, budget change or 070 implementation.
