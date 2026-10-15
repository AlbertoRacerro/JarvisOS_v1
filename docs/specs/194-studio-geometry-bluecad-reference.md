# 194 — Published Studio geometry as a BLUECAD visual assembly reference

State: **accepted and ready** under the 2026-10-15 maintainer directive, after recovery against `a6ce2259cd25c5d2b9d1a5755c54e3118bec7f72`.

Hard dependencies: 189 (merged). Spec 193 is required for the Sidecar-started golden workflow, not for manual Studio geometry references.

## Outcome

A published, parameterized Studio geometry generation can be selected as a reusable component in a BLUECAD assembly view. The reference pins the immutable Studio version and exact generated GLB/STEP/STL artifact hashes, input values and units. An engineer places or moves it in millimetres alongside typed BLUECAD parts and sees its provenance and stale/superseded status. A helical baffle demonstrates this without adding a BlueRev-specific or hardcoded part kind.

Spec 189 already provides isolated build123d authoring, immutable versions, registered hash-verified geometry runs, and standalone GLB preview. BLUECAD's current GeometrySpec accepts only fixed part kinds and its host export imports/builds those kinds. The minimum safe integration is a referenced visual component, preserving the existing typed geometry pipeline.

## Authority and scope

- Store a BLUECAD-owned reference to a same-workspace, published Studio geometry **generation**, not source text or a path supplied by the caller. Verify the version, source/contract hashes, generation inputs and artifact hashes against the Studio/runner/artifact owners when adding, loading, and serving. A newer version or changed upstream Parameter never silently changes the pinned reference; surface stale/superseded status and offer explicit re-generation/re-pin.
- Compose the referenced GLB into the BLUECAD browser assembly scene with a declared millimetre coordinate frame and explicit translation/rotation. Keep the reference's identity and transform in candidate/assembly provenance and make it selectable. Browser loading uses only the hash-verified same-origin Studio artifact route. Invalid, foreign, missing or tampered artifacts fail closed with a visible finding.
- Preserve the existing BLUECAD typed part catalogue and its kernel/export contract. A visual Studio reference is not silently included in BLUECAD's combined STEP/STL, port mating, FEM, CFD, manufacturing checks, or declared assembly volume. The UI labels this scope clearly while the original Studio STEP/STL remain available for download. A future physical-kernel import would need separate security and validation authority.

## Acceptance and evidence

1. Real browser on exact head: author/test/publish a parameterized helical baffle, generate it, add its pinned reference to a BLUECAD assembly, move/rotate it, and visualize it with a typed part. The reference card shows version, generation/input units, hashes and visual-only scope. Screenshots reflect the actual scene.
2. Deterministic tests cover same-workspace pin admission, exact artifact integrity, stale/superseded generation, transform units, repeatable scene identity, foreign/missing/tampered reference refusal, and no change in typed BLUECAD export bytes or safety findings.
3. Full relevant backend suite/Ruff, frontend build and focused browser checks pass. Software visualization does not imply the baffle is scientifically, mechanically, or manufacturably qualified.

## Non-goals

No new fixed part kind, host import of untrusted STEP/GLB into build123d, assembled STEP/STL export containing the reference, automatic re-generation, port semantics, or physical validation of the referenced component.
