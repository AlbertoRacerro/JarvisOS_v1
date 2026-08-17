# 096 — OPERATOR-WORKBENCH-CORRECTION-0

Definition status: **complete definition; readiness required before implementation**  
Derived from exact master: `914d70bfc71fc7495c97ae06ec452e69b0fce9ed`  
Depends on runtime authority: 054, 083, 088, 089, 091  
Product authority: 095 OPERATOR-WORKSTATION-AUTHORITY-1

## 1. Purpose

Apply the first bounded runtime correction required by 095 to the already-merged workstation surfaces. This slice fixes information hierarchy, containment and sidecar composition that are visibly wrong today, without inventing the engineering property/working-configuration backend semantics owned by later 071b/092/058c.

The operator outcome is a stable engineering desktop: Jarvis occupies the upper bounded part of the existing right sidecar; a bounded Properties region occupies the lower part using only real currently available selection/context information; Runs raw payloads cannot push Analysis far down the page; Review leads with the decision rather than machine identity; long opaque tokens remain inspectable without breaking layout.

## 2. Hard scope boundary

096 is a **presentation/composition correction over existing authority**. It may rearrange, progressively disclose, bound, label and locally scroll data already returned by existing APIs. It must not add a second engineering store, new model/property schema, working configuration, model selector, formula engine, scene semantic identity, lifecycle mutation, Jarvis engineering mutation, provider path, runner mutation or canonical project mutation.

If a desired Properties field cannot be obtained truthfully from existing selection/stage/runtime data, render an honest bounded empty/selection state or defer it to 071b/092/058c. Do not fabricate engineering values to make the panel look complete.

## 3. Information hierarchy applied now

096 applies 095 L0/L1/L2 rules to the surfaces it touches:

- normal headers/rows prefer human-readable route, run label/status, proposal scope and current selection meaning;
- UUID, digest, request/job id, exact ISO timestamp and raw JSON/log payload move under `Technical details`, `View raw`, `Inspect` or equivalent disclosure;
- normal timestamps are human-readable while exact values remain copyable in Audit disclosure;
- semantic labels are preferred where current authority can support them; do not translate unknown raw provenance into invented semantic provenance.

Opaque identity remains available for debugging/audit and is never destroyed.

## 4. Canonical right sidecar composition

On normal desktop, preserve the one existing 083/091 right sidecar shell and divide its content vertically:

1. **Jarvis: 40–45% of available sidecar height**;
2. **Properties: 55–60% of available sidecar height**.

The exact CSS ratio may vary within those bands to fit existing shell chrome. Both regions are bounded by the sidecar viewport and scroll internally. Opening long transcript/context/property content must not increase document/page height.

### 4.1 Jarvis upper region

Jarvis remains AI interaction only. Preserve existing 091 execution/thread/context authority and behavior. The upper region contains compact thread control/history disclosure, transcript/status, composer, and only controls already backed by real authority.

Move geometry dumps, lifecycle/debug identifiers and generic stage metadata out of the Jarvis conversational hierarchy. A compact human-readable current-context chip/line is allowed. Existing stage contribution data that cannot yet be represented as engineering Properties may remain reachable under Inspect/Technical details rather than being deleted.

Transcript is the internal scroll owner. Header/thread control and composer remain reachable without page scrolling. Closing/reopening the sidecar must preserve 091 in-flight ownership and no-redispatch behavior.

### 4.2 Properties lower region

Properties is introduced here as a **bounded composition shell**, not yet the full 071b engineering editor. It shows only truthful existing selected-object/stage context and a clear no-selection state. It may group currently authoritative fields under human headings, but must not invent future Hydraulics/Thermal/Optical/Fouling contracts.

Machine identity and raw metadata are secondary under Technical details. The lower property area owns its own vertical scroll. Its header remains visible/reachable while content scrolls.

### 4.3 Effective 200% / compact width

When available width/height makes a vertical split unusable, the same sidecar degrades to two keyboard-operable tabs, `Jarvis` and `Properties`, inside the same shell. This is responsive presentation only; it must not create two sidecars, duplicate state or remount an in-flight Jarvis request in a way that redispatches.

No global horizontal page overflow is allowed.

## 5. Runs containment correction

The existing 088 Runs authority remains read-only. 096 changes presentation only.

Raw JSON, logs, result payloads and artifact detail regions must have a bounded default max-height with internal scroll and an explicit `View raw`, `Expand` or equivalent disclosure. Expanding one technical payload must not permanently force Analytics Dock thousands of pixels below the decision/work area; an expanded/raw view may use a bounded modal/drawer/local region if that is smaller than page expansion.

Run summary/detail prioritizes human status, model/run label when available, meaningful result/value/unit information and failure reason. UUID/job/request/digest/raw payload remain available under Technical details.

Analysis/Analytics remains compositionally near the work area and retains existing 089 comparability/unit authority. 096 does not change calculations or comparability semantics.

## 6. Review correction

The existing 054 proposal authority remains unchanged. Review becomes a decision surface.

Primary content, when current data supports it:

- what is proposed;
- affected human-readable scope/object;
- current → proposed difference when both are authoritative;
- impact/evidence only when already authoritative;
- existing Accept/Reject or other already-authorized decision actions.

UUID, request/job ids, exact timestamps, digests and raw payloads move under Technical details. If current backend does not provide a truthful current value or impact, omit that comparison instead of manufacturing one.

096 does not add proposal mutation types, promotion authority, engineering-record edit, grading or Jarvis action execution.

## 7. Global containment and hostile data

All touched cards/rows must tolerate long unbroken UUIDs, digests, paths, model names and hostile markup-like text.

- no page-level horizontal overflow;
- machine tokens wrap/truncate visually with a deliberate copy/inspect path where one already exists or can be added locally without new backend authority;
- raw text remains inert; no HTML execution or unsafe Markdown path is introduced;
- technical payloads scroll locally;
- focus must not become trapped in a scroll region.

## 8. State ownership and races

096 must preserve current canonical owners.

- Jarvis App/controller ownership from 091 survives visual tab/split changes;
- route/workspace/selection stale-response guards are not weakened;
- Properties presentation derives from current selection/stage data and must reject/ignore stale visual selection completion under the same existing ownership rules;
- opening/closing disclosure or switching Jarvis/Properties responsive tabs is local UI state only and causes zero backend mutation;
- Analytics composition is not replaced when sidecar composition changes;
- no presentation transition may trigger provider, runner, proposal or engineering mutation.

## 9. Accessibility and responsive acceptance

Implementation must prove:

- keyboard can reach Jarvis thread control, transcript, composer, Properties, Technical details, Runs raw disclosures and Review actions;
- responsive `Jarvis | Properties` tabs expose correct tab semantics/focus and do not lose the in-flight Jarvis state;
- effective 200% zoom remains usable with no global horizontal overflow;
- reduced-motion behavior remains inherited from 070;
- light/dark/system appearance remains inherited;
- internal scroll areas remain discoverable and do not hide the composer or primary decision action;
- Escape/focus-return behavior already owned by the sidecar remains intact.

## 10. Expected minimum implementation boundary

Readiness must verify the smallest path allow-list from exact current master. Expected candidates are limited to existing shell/sidecar presentation, Jarvis sidecar local CSS/content composition, Runs presentation/styles, Review presentation/styles, and one focused 096 checker/browser evidence lane. App/Layout changes are allowed only if exact current composition proves they are the minimum place to create the two bounded regions; no shell architecture rewrite.

No backend product code, schema/migration, provider/egress/runner code, package/dependency change, new state store or global visual-identity lane is expected.

## 11. Non-goals / explicitly deferred

096 does not implement:

- full engineering property contracts or editable values — 071b;
- working configuration, dirty baseline, Undo/Revert semantics — 071b;
- deterministic preflight/run-start history semantics — 071b;
- stable scene → engineering object identity — 092;
- property groups/model-choice/formula/dependency semantics — 058c;
- Jarvis structured engineering changes/safe fixes — 097;
- Engineering Data Edit/Active/Inactive/Archive/Supersede/Delete — 098;
- variants/comparison — 006b/058b;
- permanent `Was this useful?` grading — 062 remains deferred secondary Evaluation/Audit;
- Notes/scratchpad;
- spreadsheet/bulk editing;
- global visual identity redesign.

## 12. Deterministic acceptance

A focused checker must fail if implementation:

1. creates a second sidecar or removes existing 091 ownership;
2. removes Runs Analytics composition;
3. introduces direct provider/task execution from frontend;
4. introduces backend/schema/package/workflow scope outside a separately justified evidence-only lane;
5. leaves known raw JSON/log/result containers unbounded by default;
6. promotes UUID/digest/raw JSON to primary Review/Properties/Jarvis labels contrary to this definition;
7. adds future engineering values/contracts not present in current authority.

Source checks are necessary but not sufficient.

## 13. Browser evidence matrix

Exact-head browser proof must exercise at minimum:

1. normal desktop sidecar: Jarvis upper ~40–45%, Properties lower ~55–60%, both locally scrollable, document height stable while long transcript/property content is exercised;
2. Jarvis long transcript keeps composer/header reachable;
3. Properties long content scrolls internally and exposes Technical details without page overflow;
4. effective-200%-like compact viewport degrades to one `Jarvis | Properties` tabset with keyboard operation and no duplicate sidecar;
5. held/in-flight Jarvis submit survives responsive tab switch and sidecar close/reopen with exactly one interaction dispatch;
6. Runs long raw JSON/log/result payload remains bounded and Analysis remains reachable without extreme page scroll;
7. Review long IDs/raw detail are secondary while proposal/decision actions remain primary and reachable;
8. hostile markup-like payload renders inertly;
9. long unbroken tokens do not create global horizontal overflow;
10. route/workspace/selection transitions do not allow stale Properties/Jarvis presentation to repaint current context;
11. zero unexpected provider/external calls or product mutations are caused by presentation/disclosure interactions;
12. keyboard, focus return, Escape, reduced motion and light/dark/system contracts remain intact.

Evidence records the exact implementation SHA. Any product-head mutation invalidates browser evidence and independent review.

## 14. Rollback

096 must be independently removable. Reverting it restores the current merged 083/088/089/054/091 presentation without data migration or rollback of AI threads, runs, proposals, analytics, settings or BLUECAD artifacts. No durable data created by 096 is required for rollback.

## 15. Readiness questions

Before implementation, derive a separate readiness record from fresh master and answer:

1. Which exact current components/CSS own sidecar height, Jarvis transcript, stage context, Runs raw payloads, Analytics composition and Review detail?
2. Can the 40–45/55–60 split be achieved without changing Layout authority, and what is the minimum path if not?
3. What truthful existing selection/stage data can Properties show before 071b/092 without inventing engineering semantics?
4. Which current Runs payload containers cause page-height expansion and what bounded disclosure preserves complete raw access?
5. Which Review fields are authoritative enough for current→proposed/impact and which must remain omitted?
6. What exact stale/in-flight behaviors from 091/083 must the responsive tab composition preserve?
7. What exact implementation allow-list is sufficient with zero backend/schema/provider/package/global-identity change?
8. What exact browser fixtures prove internal scroll, stable page geometry, effective 200%, hostile long data, no redispatch and Analytics/Review continuity?

Registry row 096 remains `planned`; this definition alone grants no runtime implementation authority.