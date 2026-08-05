# Spec 083 amendment — reconcile the UI foundation checker

**Status:** normative amendment to `docs/specs/083-app-shell-1.md` sections 16–18.

**Exact finding baseline:** `2d0fe06d19e3f7436ba206b501b7b41df4fdb5c5`

## 1. Verified blocker

On current canonical master, `docs/specs/STATUS.md` correctly records:

```text
070 | merged | implementation PR #225
```

The merged `scripts/check_ui_foundation.py` still requires:

```text
070 | in_review | implementation PR #225
```

Therefore the checker fails against the correct post-merge registry state. Requiring the checker unchanged during 083 would make the implementation contract internally impossible: the implementation must either fail a mandatory gate or modify a file excluded by the exact file set.

## 2. Authorized minimum repair

The single 083 implementation PR is additionally authorized to modify:

```text
scripts/check_ui_foundation.py
```

The only permitted semantic change in that file is:

- update `check_registry()` so row 070 must be `merged` and linked to implementation PR #225;
- update the associated failure text accordingly;
- add or adjust a bounded in-memory self-case only when necessary to prove that `merged/#225` passes and stale `in_review`, wrong PR, missing row, or another status fails.

No token, theme, primitive, migration, color, inline-style, SVG, responsive, BLUECAD, or other checker rule may be weakened, removed, bypassed, or made warning-only.

## 3. Exact-file-set amendment

Section 16 of the full spec is amended as follows:

```text
Authorized modified files += scripts/check_ui_foundation.py
```

All other exact-file-set restrictions remain binding.

## 4. Gate behavior

On the exact implementation head, both must pass:

```text
python scripts/check_ui_foundation.py
python scripts/check_app_shell.py
```

The repaired foundation checker remains a mandatory gate. It is not replaced by the shell checker.

## 5. Scope and rollback

This repair:

- changes no runtime behavior;
- changes no registry row;
- changes no 070 foundation contract;
- adds no dependency;
- is independently reviewable in the 083 implementation diff;
- rolls back with the 083 implementation only if the registry expectation is otherwise restored to an equivalent valid post-merge check.

The amendment closes only the stale lifecycle assertion. It grants no authority to redesign or relax spec 070.
