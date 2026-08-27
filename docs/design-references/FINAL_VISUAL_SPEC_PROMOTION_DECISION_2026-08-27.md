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

`100c FINAL-PRODUCT-DIRECTION-AUTHORITY-0` is the maintainer's intended future insertion **after 100b and before 101**.

This document records that intent but is not live queue authority. `docs/specs/STATUS.md` remains the sole authority for whether 100c actually occupies that position and when it may start.

The intended sequence, once separately reconciled into `STATUS.md`, is:

1. complete 100a through its normal lifecycle;
2. complete 100b through its normal lifecycle/disposition;
3. perform a separately authorized docs-only registry reconciliation that inserts/activates 100c if the maintainer still chooses this direction after exact post-100b inspection;
4. execute 100c as documentation/authority re-derivation only after `STATUS.md` authorizes it;
5. only then proceed through the queue produced by that re-derivation.

100c must not mechanically promote every pseudo-spec. It must classify overlap, retain one canonical owner, eliminate unnecessary slices, and decide which existing 101–110 remain valid/rederived/reordered.

## Builder behavior

External builders must continue to follow live `STATUS.md`. This planning decision alone does **not** authorize them to insert 100c, divert from 101, or implement any FV draft. If 100b finishes while 100c is absent from `STATUS.md`, a separate maintainer/coordinator-authorized registry reconciliation is required before 100c can become the next queue item.

The draft pack is planning evidence, not a parallel queue.
