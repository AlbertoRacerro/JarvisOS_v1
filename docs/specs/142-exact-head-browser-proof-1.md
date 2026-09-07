# 142 EXACT-HEAD-BROWSER-PROOF-1

## Status

Planning/readiness candidate. The canonical lifecycle state remains `docs/specs/STATUS.md`.

## Goal

Remove maintainer-local browser work from the normal beta delivery path by providing reusable, deterministic, exact-head browser evidence on GitHub-hosted infrastructure.

The capability must let a frontier coordinator prove accepted visible/runtime behavior for an implementation PR without depending on a personal PC, a self-hosted runner, provider credentials, or a human screenshot session.

## Product outcome

For a supported scenario, one GitHub-hosted proof run must:

1. receive or resolve an explicit repository, PR, expected PR-head SHA, and scenario identity;
2. verify the requested PR/head relationship against fresh GitHub truth, then check out exactly that candidate SHA and fail closed if the checked-out SHA differs;
3. start the required JarvisOS backend/frontend from that exact tree with isolated proof-only data;
4. run a real Chromium browser through Playwright;
5. execute the scenario assertions against the rendered application and supporting same-runtime API identity where required;
6. emit durable machine-readable proof plus human-inspectable screenshots/trace/logs;
7. bind every produced artifact to the exact candidate head so any material head mutation invalidates the evidence rather than silently carrying it forward.

The proof controller is not candidate-owned evidence. Workflow/control logic, scenario assertions, verdict generation, and manifest construction must execute from a trusted merged 142 owner (normally the default-branch workflow/harness or an equivalently immutable trusted checkout) while the candidate source is checked out separately as the system under test. Candidate-controlled files may provide application behavior and test data only where explicitly allowed; they must not be able to weaken assertions, rewrite the final verdict, or redefine what constitutes PASS.

## Initial beta-critical scenarios

The first implementation is intentionally narrow. It must support only the currently blocked beta proof families unless a directly causal sibling is required.

### 113 `/memory/models`

Prove the accepted 113 browser gate on the exact PR head, including:

- truthful empty state;
- at least two exact model versions remain distinguishable and selecting a version renders only that selected exact-version dossier identity;
- no edit/save/approve/run/provider/filesystem/GitHub mutation affordance is exposed by the dossier surface.

### 124 `/settings/ai`

Once the 124 candidate has no known blocking semantic finding, prove the accepted exact-head Settings behavior from its active spec/readiness. The proof must remain secret-free and must not make live provider calls or require provider credentials.

### 140 `/coding/repository` and `/coding/runtime`

Once the 140 candidate has no known blocking semantic finding, prove the accepted exact-head Coding repository/runtime behavior from its active spec/readiness, including truthful exact-SHA/runtime identity and the absence of browser-held GitHub/provider/filesystem mutation authority.

## Proof artifact contract

Every successful or failed scenario must emit one manifest that is sufficient to determine exactly what was proved. At minimum it records:

- repository identity;
- PR number when applicable;
- expected head SHA;
- fresh GitHub-resolved PR head SHA;
- checked-out head SHA;
- base SHA or base ref when relevant;
- workflow/run identity;
- trusted proof-controller source identity;
- scenario identity and proof-data seed/version;
- browser and Playwright versions;
- backend/frontend version or exact source identity where available;
- start/end timestamps;
- each required assertion and PASS/FAIL result;
- screenshot, trace and relevant log artifact names;
- digests for proof artifacts where practical;
- final proof verdict.

A proof whose fresh PR head or checked-out SHA differs from the requested exact head is invalid even if all UI assertions pass. A proof whose assertion/verdict controller is candidate-controlled is also invalid.

## Isolation and authority

- Use only standard GitHub-hosted runners suitable for the public repository; no paid/larger runner is authorized.
- The proof must remain useful with zero local/self-hosted workers registered.
- Use isolated proof-only runtime data. It must not depend on or mutate a maintainer data root.
- No personal-PC, desktop-control, local browser, or maintainer-presence dependency.
- No provider credentials, provider live calls, arbitrary external-service credentials, or browser-side GitHub credentials.
- The trusted proof job must use least privilege, must not expose repository/provider secrets to candidate code, and must not persist checkout credentials into the candidate worktree. Candidate execution occurs only in the ephemeral GitHub-hosted runner with a bounded job timeout.
- The candidate PR/head relationship is checked from fresh GitHub truth before candidate execution and the local checkout identity is checked again before any PASS can be emitted.
- Browser proof is evidence only. It grants no product mutation, Git push, PR merge, STATUS mutation, provider execution, or external side-effect authority.
- Static source inspection, source-string tests, API-only checks, mocked DOM assertions, or fake screenshots cannot substitute for a required real-browser scenario.
- Normal deterministic CI and semantic review remain separate gates; 142 does not replace them.

## Triggering and convergence

The implementation should make proof cheap enough to run whenever a beta-critical candidate reaches a frozen head that actually needs browser evidence. It need not run expensive scenarios on every intermediate repair commit if the candidate is already known to require material changes.

A new material candidate-head commit invalidates prior browser evidence for that candidate and requires a new proof run before merge when the active acceptance contract requires browser evidence.

The frontier coordinator may choose the smallest maintainable GitHub Actions/Playwright structure that satisfies this contract. This spec does not require a general browser-testing framework, a generic visual-regression platform, or a new orchestration service.

## Acceptance

142 is complete when repository evidence proves all of the following on the merged implementation:

1. a standard GitHub-hosted runner can perform a real Chromium proof from an explicit exact candidate SHA;
2. requested PR/head mismatch, wrong checkout identity, and candidate-controlled proof-controller substitution are refused before a PASS can be emitted;
3. isolated proof-only JarvisOS runtime startup is deterministic enough for the supported scenarios;
4. 113, 124 and 140 scenario entry points exist and produce scenario-bound manifests/artifacts, with scenarios allowed to refuse when the corresponding candidate is not semantically ready;
5. screenshots plus Playwright trace/relevant logs are retained as workflow artifacts on failure and success where useful;
6. the manifest binds proof to repository/PR/head/scenario/run identity, trusted proof-controller identity, and assertion results;
7. zero local workers and zero maintainer PC interaction are required;
8. no paid runner, provider credential/live provider call, personal secret, persisted candidate checkout credential, browser-side GitHub authority, or fake/static substitute proof is introduced;
9. at least one real exact-head beta-critical scenario is exercised end to end through the new capability before or immediately after merge, demonstrating that the capability can replace the previous maintainer-local proof path.

## Non-goals

- pixel-perfect visual regression or aesthetic approval;
- a generic browser automation product;
- personal-PC automation;
- self-hosted runner management;
- Hermes/tool orchestration;
- local-worktree actuation (141);
- provider smoke testing;
- paid CI acceleration;
- replacing deterministic CI, semantic review, or exact-head merge/CAS rules.

## Cost constraint

Default incremental monetary cost for this capability is **EUR 0**. Standard GitHub-hosted runners for the public repository and free/open-source browser tooling are the intended execution substrate. Any future paid runner, paid service or metered external dependency requires separate explicit maintainer approval and is outside 142.
