TEMPORARY RECONCILIATION INSTRUCTION — DELETE IN THE SAME COMMIT AS THE STATUS UPDATE

Base commit: e40dd0c5c0c931156040b3209d6de0514d58002b
Merged implementation: PR #231

Edit only docs/specs/STATUS.md and delete this temporary file.

Exact replacement 1:
OLD: 3. Spec 070 UI-FOUNDATION-1 remains merged and reconciled; spec 083 APP-SHELL-1 is `in_review` in implementation [PR #231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231). The Penpot visual-identity work remains a separate independently removable lane.
NEW: 3. Specs 070 UI-FOUNDATION-1 and 083 APP-SHELL-1 are merged and reconciled; spec 084 BLUECAD-READ-MODEL-1 remains the next planned frontend-beta slice. The Penpot visual-identity work remains a separate independently removable lane.

Exact replacement 2:
OLD: | 083 | in_review | [#231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231) | APP-SHELL-1 | 006, 070 | Implementation PR #231 implements only the identity-independent shell under [the 2026-08-05 readiness decision](083-readiness-2026-08-05.md) and the [complete APP-SHELL-1 specification](083-app-shell-1.md), including the bounded [UI-foundation checker reconciliation](083-ui-foundation-checker-amendment-2026-08-05.md) and [production SPA fallback](083-spa-fallback-amendment-2026-08-05.md); Penpot visual identity remains separate and independently removable. |
NEW: | 083 | merged | [#231](https://github.com/AlbertoRacerro/JarvisOS_v1/pull/231) | APP-SHELL-1 | 006, 070 | PR #231 merged the identity-independent shell under [the 2026-08-05 readiness decision](083-readiness-2026-08-05.md) and the [complete APP-SHELL-1 specification](083-app-shell-1.md), including the bounded [UI-foundation checker reconciliation](083-ui-foundation-checker-amendment-2026-08-05.md) and [production SPA fallback](083-spa-fallback-amendment-2026-08-05.md); Penpot visual identity remains separate and independently removable. |

Do not change row 084 or any other line. Final diff must contain only docs/specs/STATUS.md with exactly two one-line replacements.