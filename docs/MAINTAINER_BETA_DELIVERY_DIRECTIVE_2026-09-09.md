# Maintainer beta delivery directive — 2026-09-09

Status: current scheduling directive
Authority: maintainer scheduling only; does not itself widen any accepted product, security, credential, egress, Git, filesystem, execution, or merge authority.

## Operating requirement

JarvisOS development and repository delivery must be able to continue **cloud-only and unattended**, without requiring any maintainer-owned PC, laptop, workstation, home network, or future personal server to be powered on or available.

The maintainer's personal hardware is not part of the normal development critical path. A local machine may be used only when a task intrinsically requires local hardware/data or when the maintainer deliberately chooses to activate an optional local capability. Ordinary source work, tests, branch delivery, PR progression and beta convergence must not depend on it.

## Reclassification of 141

**141 LOCAL-WORKTREE-ACTUATOR-1 remains merged and useful, but it is an optional local execution/delivery plane, not the primary solution for cloud repository delivery.**

141 may later serve tasks that genuinely need local files, devices, GPU/desktop resources, OS-owned credentials, or a dedicated always-on host. Its existence must not create a requirement that a maintainer-owned computer be online for ordinary autonomous development.

Fresh evidence from #589 shows that a cloud worker can complete and verify useful work yet still lack a Git remote or usable GitHub network path. Routing that work to a maintainer PC would merely move the bottleneck rather than remove it.

## Immediate beta-critical objective: cloud-native trusted delivery

Derive and implement the **smallest safe cloud-native trusted delivery bridge** needed to close the demonstrated `LOCAL_ONLY` / `DELIVERY_FAILURE` class without maintainer hardware.

Preferred shape is existing repository-owned / GitHub-hosted infrastructure, especially GitHub Actions where it is already the smallest compatible owner. An equivalent cloud-native repository-owned mechanism is acceptable if fresh evidence shows it is safer or smaller. Do not create a new orchestration platform when an existing trusted plane can own the mutation.

The required outcome is:

1. an incapable model/cloud worker produces a complete durable delivery payload bound to an exact base SHA, intended target ref, changed paths and verification evidence;
2. that payload survives the requesting session and is stored in a repository-consumable cloud location;
3. a trusted cloud-side writer independently re-reads the current remote head and validates admission, sensitive paths and expected-old-head / fast-forward conditions;
4. the trusted writer materializes the already-authorized delta in an ephemeral checkout, runs the required bounded verification, commits and updates only the intended non-default PR branch;
5. the resulting remote SHA is independently re-read and reported so ordinary CI, review and browser-proof lanes can continue.

The model must not receive raw GitHub credentials. Prefer repository/workflow-owned short-lived credentials such as the existing GitHub Actions `GITHUB_TOKEN` boundary. Preserve exact-head/CAS semantics and all accepted protections from existing 022/079/141 delivery owners where reusable.

## Acceptance properties

The cloud-native bridge is not complete merely because it can run a workflow. It must demonstrate end-to-end that:

- the maintainer's PC can be off;
- no self-hosted runner or personal host is required for the ordinary path;
- a durable patch produced by an environment with no Git remote can still become a remote commit on the intended existing PR branch;
- stale remote head, third-party branch movement, sensitive/control-path widening and malformed/incomplete payloads fail closed;
- credentials remain inside the trusted cloud mutation boundary and are never exposed to model-authored code or payload content;
- no merge, default-branch mutation, force/history rewrite, arbitrary branch creation, generic shell/PTY, arbitrary filesystem, provider credential, desktop or self-update authority is added merely to solve delivery;
- zero optional local workers leaves the cloud development path fully usable.

Use **#589 / spec 143** as the first concrete acceptance case when practical: the already-demonstrated complete durable spec-143 patch should be materializable onto the existing `impl/143-operator-semantic-ux` branch without any maintainer computer participating.

## Post-143 infrastructure objective: generic builder toolbox

After the currently active spec-143 product family and its already-established trusted browser-proof compatibility work, including #589/#594, have converged, the next infrastructure priority is a **bounded tooling-generalization pass** over the browser-proof stack and other infrastructure added in the recent beta-convergence work.

The purpose is not a broad rewrite. It is to ensure that infrastructure intended to be used by builders behaves as a reusable **capability-oriented toolbox**, rather than as one-off implementation logic tied to the spec that first required it.

The target properties are:

1. **Generic capability, task-specific intent.** A tool should expose reusable bounded operations; a spec/task/proof plan should decide how those operations are composed for the current goal.
2. **Browser proof separation.** The trusted Chromium environment should become a generic policy-bound browser executor. Spec/task-specific verification should be expressed through declarative proof plans or an equivalently bounded data representation, rather than permanent `prove<spec>` control logic and hard-coded presentation strings in the trusted engine.
3. **No arbitrary model-authored privileged code.** Genericity must not mean executing arbitrary JavaScript, shell, Python, workflow, or equivalent code supplied by the model inside a privileged trusted lane. Use a closed, validated primitive vocabulary where needed.
4. **Reusable delivery/test/review/evidence primitives.** Audit recent delivery, test, review, browser, evidence and recovery infrastructure for avoidable coupling to one spec, branch, UI surface or payload shape. Refactor only where fresh evidence shows such coupling prevents ordinary future reuse.
5. **Compatibility, not permanent special cases.** Existing 113/124/140/143 scenarios should serve as migration and regression cases for the generic mechanism, not as permanent architecture-specific branches inside the underlying tool.
6. **No authority widening for convenience.** Preserve exact-head/CAS, trusted-controller ownership, credential isolation, candidate isolation, sensitive-path controls, fail-closed behavior and all existing security/egress/destructive boundaries.
7. **Do not generalize already-generic owners unnecessarily.** If an existing primitive is already task-neutral and reusable, leave it alone. Prefer measured evidence over aesthetic abstraction.
8. **Future-spec usability.** A normal future spec should be able to use the toolbox by selecting/configuring existing safe capabilities and task-specific plans, without requiring a new infrastructure implementation merely because the feature semantics changed.

The coordinator owns the minimum architecture and migration path. The first pass should explicitly inventory recent infrastructure as `GENERIC AS-IS`, `GENERALIZE`, `ABSORB`, or `RETIRE/REPLACE`, with concrete evidence for any mutation.

## Priority order

1. Keep 124 and 141 as merged canonical foundations; do not reopen them merely to relabel scheduling intent.
2. Preserve the now-demonstrated cloud-native trusted delivery path and repair only measured defects; do not reopen its architecture without evidence.
3. Finish and converge the currently active beta-critical 143 product family and the already-established #594 trusted browser-proof compatibility work using the current proof stack where that remains the shortest safe path.
4. Do **not** delay that 143/#594 closure merely to generalize tooling first.
5. Immediately after those accepted product/proof obligations converge, perform the bounded tooling-generalization pass described above before starting lower-value infrastructure expansion.
6. After the generic toolbox pass, continue beta-critical product work using the generalized capabilities, and simplify measured lifecycle/delivery/bookkeeping duplication where fresh evidence justifies it.

This is scheduling/goal authority, not permission to waive dependency, review, exact-head, CI, browser-proof, security or merge gates. The implementation coordinator owns the minimum architecture, spec/readiness corrections and reuse decisions needed to reach the outcome.

## Delivery failure rule

A deterministic delivery-capability failure such as no Git remote, stable proxy/HTTP 403, or unavailable credentials in the acting model environment must not cause indefinite regeneration or repeated identical attempts in that same lane.

After one confirmed same-cause failure, unless material evidence changes:

1. persist the complete consumable patch/delta with exact base identity, target ref, changed-file list and focused verification evidence in a cloud/repository-consumable form;
2. route it to the trusted cloud delivery owner rather than a maintainer-owned PC;
3. if that trusted cloud owner is not yet available, classify the work truthfully as `DELIVERY_BLOCKED`/`LOCAL_ONLY` as applicable and preserve the payload for later consumption;
4. do not solve the problem by exposing credentials to the model or widening force/merge/default-branch authority.

A local actuator may be used only as an optional fallback when the maintainer explicitly chooses it or the task intrinsically requires local resources; it is not the default recovery target for ordinary repository work.

## Expiry

This directive replaces the earlier same-day interpretation that treated 141/local-host delivery as sufficient for the cloud delivery bottleneck.

It remains current until the cloud-native trusted delivery path, the beta-critical 143/#594 path, and the bounded tooling-generalization pass have converged, or until explicitly superseded by a newer maintainer directive. Long-lived generic rules should then be folded into existing canonical governance only where repeated evidence still justifies them.
