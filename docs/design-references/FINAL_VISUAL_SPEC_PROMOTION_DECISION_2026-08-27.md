# Maintainer decision — final visual direction implementation promotion — 2026-08-27

Status: explicit maintainer planning decision; no runtime implementation authority by itself.

## Decision

The maintainer considers the visual/product design inspection complete and wants the approved operator-product direction preserved so it can be implemented through normal specifications rather than remaining only in mockups/chat context.

The repository therefore records:

- PD-08 as the final product-direction reconciliation after the visual pass;
- `docs/spec-drafts/FINAL_VISUAL_IMPLEMENTATION_PACK_2026-08-27.md` as the complete planning draft set for backend/domain/frontend work discovered during that pass;
- `docs/specs/100c-final-product-direction-authority-0.md` as the definition-only queue-rederivation kernel that must reconcile those drafts against exact post-100a/100b master and existing 101–110 before runtime implementation;
- `docs/design-references/coding-beta/CODING_RUNTIME_TERMINAL_FUTURE_2026-08-27.md` as the future approved integrated-terminal direction.

## Queue insertion intent

`100c FINAL-PRODUCT-DIRECTION-AUTHORITY-0` is intended to be inserted into the binding queue **after 100b and before 101**.

This decision does not make 100c implementation-ready and does not change the current `100a=planned` front. The canonical sequence remains:

1. complete 100a through its normal lifecycle;
2. complete 100b through its normal lifecycle/disposition;
3. reconcile `STATUS.md` to insert/activate 100c if the row is not already present;
4. execute 100c as documentation/authority re-derivation only;
5. only then proceed through the newly re-derived runtime queue.

100c must not mechanically promote every pseudo-spec. It must classify overlap, retain one canonical owner, eliminate unnecessary slices, and decide which existing 101–110 remain valid/rederived/reordered.

## Builder behavior

External builders may use this explicit maintainer decision to perform the **docs-only registry insertion/reconciliation** for 100c after 100b if `STATUS.md` has not yet been updated. They may not use this document to skip `STATUS.md`, start 100c before 100b, or implement any FV draft directly.

The draft pack is planning evidence, not a parallel queue.
