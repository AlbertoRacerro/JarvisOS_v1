# Maintainer-approved product direction packet

Status: **future product direction; not implementation authority**  
Approved in maintainer design session: 2026-08-26; final visual/product reconciliation: 2026-08-27  
Owner: repository maintainer

This directory freezes product decisions that were previously at risk of existing only in chat context. These files are deliberately more precise than ordinary brainstorming notes: they define intended product semantics, navigation, ownership boundaries, non-goals, and future backend responsibilities so that later specification authors do not reinterpret the maintainer's decisions.

They are **not** entries in the implementation queue and do not authorize runtime work by themselves.

`docs/specs/STATUS.md` remains the sole source of live spec status, queue order and implementation authority. The post-100 maintainer visual-inspection hold was explicitly released on 2026-08-27 and that release is already registry-reconciled; the next live front remains whatever `STATUS.md` says. A future definition/authority specification must promote the relevant parts of this packet into the canonical spec queue before a builder may implement them.

If these files conflict with current runtime behavior, current runtime behavior remains factual current state while this packet records the intended replacement direction. If they conflict with a later accepted ADR/spec, the later accepted authority wins.

## Frozen global information architecture

Normal primary navigation is intended to become exactly:

1. `Design`
2. `Memory`
3. `Development`
4. `Coding`
5. `Settings`

There is no normal `Home`, `Runs`, `Engineering Data`, or `Review` primary destination in the target product architecture.

Detailed contracts:

- [`01-operator-information-architecture.md`](01-operator-information-architecture.md)
- [`02-design-workbench-contract.md`](02-design-workbench-contract.md)
- [`03-project-memory-and-development-contract.md`](03-project-memory-and-development-contract.md)
- [`04-coding-and-self-development-contract.md`](04-coding-and-self-development-contract.md)
- [`05-settings-contract.md`](05-settings-contract.md)
- [`06-future-spec-decomposition.md`](06-future-spec-decomposition.md)
- [`07-model-change-validation-and-reconciliation.md`](07-model-change-validation-and-reconciliation.md)
- [`08-final-visual-product-contract.md`](08-final-visual-product-contract.md) — **final 2026-08-27 reconciliation layer; where more specific, PD-08 supersedes earlier packet prose for future product composition.**

For frontend/product-facing promotion work, also read:

- `docs/design-references/APPROVED_OPERATOR_UI_MANIFEST_2026-08-27.md` — canonical HTML index, exact reference viewport/hash/blob identity and final cross-surface overlays;
- `docs/design-references/FRONTEND_CONFORMANCE_CONTRACT_2026-08-27.md` — mandatory translation/conformance rules for production frontend;
- the most-specific approved surface reference under `docs/design-references/`.

These visual/reference documents define intended composition but do not grant runtime/backend authority.

## Promotion rule

A future real specification derived from this packet must:

- cite the exact product-direction file(s) it promotes, including PD-08 whenever the promoted behavior intersects the final visual/product reconciliation;
- for frontend/product-facing work, cite the canonical manifest/conformance contract and exact selected HTML/reference identity;
- preserve every explicit invariant and non-goal unless the maintainer explicitly revises it;
- identify any current route/component/schema that is being replaced rather than silently retaining both concepts;
- keep user-facing concepts separate from storage/database implementation concepts;
- avoid creating a second competing memory, provider, orchestration, artifact, repository, Roadmap/Calendar, or runtime state store where current canonical infrastructure can be extended;
- define migration/compatibility behavior explicitly where current canonical records already exist;
- preserve every approved visible capability as implementation work when backend support is missing rather than redesigning it away;
- reconcile every semantically overlapping live/planned `STATUS.md` row before allocating new canonical ownership.

## Visual-reference rule

Approved HTML references are normative implementation targets at their manifest reference viewport, subject to the final cross-surface overlays recorded in the manifest. They are stronger evidence for layout/composition than screenshots rendered incorrectly by tooling.

When an approved HTML and a screenshot disagree because of rendering/tooling error, the approved HTML is authoritative. Fixture/demo values inside a reference are not runtime truth: production must replace them with real backend/runtime data or a truthful loading/empty/unavailable state without changing the approved composition.

An intentional deviation from the canonical visual/product reference requires a new explicit maintainer decision and an updated canonical reference/manifest identity; an implementation PR may not silently establish a replacement design.
