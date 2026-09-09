# Maintainer beta delivery directive — 2026-09-09

Status: current scheduling directive
Authority: maintainer scheduling only; does not widen any accepted product, security, credential, egress, Git, filesystem, execution, or merge authority.

## Direction

For current beta convergence, treat **141 LOCAL-WORKTREE-ACTUATOR-1** as beta-critical enabling infrastructure alongside convergence of **124 PROVIDER-SETTINGS-GENERIC-1** and before allowing non-critical UX or roadmap work to consume the delivery critical path.

Fresh repository evidence has repeatedly demonstrated the exact problem 141 was accepted to solve: useful, tested, bounded repair work can remain `LOCAL_ONLY` or become `DELIVERY_FAILURE` when a cloud/Codex execution environment has no usable Git remote or its network/proxy path returns HTTP 403. This is now an active beta throughput bottleneck, not a hypothetical future capability.

The intended value of 141 is a **trusted delivery handoff**. It does **not** give cloud/model workers GitHub credentials. Durable local work must survive requester/session loss and may later be delivered by an authorized trusted local actuator using OS-owned credentials under the already-accepted exact-head, expected-remote-head, guarded fast-forward/CAS contract.

## Priority order

1. Converge 124 through its real deterministic, semantic and browser evidence gates.
2. Converge 141 to the **smallest safe accepted capability** that closes the demonstrated `LOCAL_ONLY` / `DELIVERY_FAILURE` bridge.
3. Continue 143 OPERATOR-SEMANTIC-UX-1 as beta-critical UX work as its hard dependencies permit.
4. After those fronts converge, simplify measured delivery/bookkeeping bottlenecks such as duplicated stale-prone lifecycle state where doing so is safe and useful.

This order is scheduling guidance, not permission to waive dependencies, acceptance criteria, exact-head evidence, required independent review, or current STATUS truth.

## Delivery failure rule

A deterministic delivery-capability failure such as:

- no configured/usable Git remote in the acting environment;
- a stable environment/proxy denial such as `CONNECT tunnel failed, response 403`;
- an unavailable approved local credential adapter;

must not cause indefinite regeneration or repeated identical delivery attempts in the same incapable lane.

After one confirmed same-cause failure, unless material evidence changes:

1. preserve the useful work in a recoverable form with exact base/head identity, complete patch or committed delta, focused verification evidence, and intended target ref;
2. route that work to an already-authorized delivery-capable owner/worker when one exists;
3. otherwise classify the state truthfully as `LOCAL_ONLY`, `DELIVERY_FAILURE`, or `BLOCKED` as applicable and continue other authorized non-conflicting work;
4. never solve the delivery problem by exposing credentials to the model, weakening repository mutation boundaries, bypassing expected-head/CAS, or broadening force/merge/default-branch authority.

Repeated `LOCAL_ONLY` / `DELIVERY_FAILURE` evidence is positive evidence for prioritizing an already-accepted bounded delivery plane that directly closes that failure family.

## 141 scope remains bounded

Prioritizing 141 does not authorize scope expansion. In particular it does not authorize PTY, generic shell/process execution, arbitrary filesystem access, self-update, browser/desktop authority, raw-token exposure, arbitrary remote-branch creation, force/history rewrite, merge, or default-branch mutation.

If the current 141 implementation head is genuinely frozen and remaining work is only consumable review/merge or a bounded security/authority-critical repair, converge it rather than parking it behind unrelated non-security work.

## Expiry

This directive is temporary. It is superseded when the maintainer explicitly replaces it or when 124, 141 and the beta-critical 143 dependency path have converged and fresh evidence no longer shows delivery as a beta bottleneck. Long-lived generic process rules should then be folded into existing canonical governance only if repeated evidence still justifies them; do not preserve this file as permanent ceremony merely because it existed.
