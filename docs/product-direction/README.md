# Maintainer-approved product direction packet

Status: **future product direction; not implementation authority**  
Approved in maintainer design session: 2026-08-26  
Owner: repository maintainer

This directory freezes product decisions that were previously at risk of existing only in chat context. These files are deliberately more precise than ordinary brainstorming notes: they define intended product semantics, navigation, ownership boundaries, non-goals, and future backend responsibilities so that later specification authors do not reinterpret the maintainer's decisions.

They are **not** entries in the implementation queue and do not authorize runtime work by themselves.

`docs/specs/STATUS.md` remains the sole source of live spec status, queue order and implementation authority. The post-100 maintainer visual-inspection hold remains in force until explicitly released. A future definition/authority specification must promote the relevant parts of this packet into the canonical spec queue before a builder may implement them.

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

## Promotion rule

A future real specification derived from this packet must:

- name the exact product-direction file(s) it promotes;
- preserve every explicit invariant and non-goal unless the maintainer explicitly revises it;
- identify any current route/component/schema that is being replaced rather than silently retaining both concepts;
- keep user-facing concepts separate from storage/database implementation concepts;
- avoid creating a second competing memory, provider, orchestration, artifact, or repository state store where current canonical infrastructure can be extended;
- define migration/compatibility behavior explicitly where current canonical records already exist.

## Visual-reference rule

Approved HTML mockups are stronger evidence for layout/composition than screenshots rendered incorrectly by tooling. When an approved HTML and a screenshot disagree because of rendering/tooling error, the approved HTML is authoritative.
