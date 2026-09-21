# Spec 144 Memory verification checkpoint

2026-09-16. Memory slice verified against the current working tree; this is not
whole-spec acceptance, provider-availability proof, or merge authorization.

## Implemented behavior

Literature registers citation metadata and raw claim/datum findings through the
existing backend owner, preserves retry keys, and exposes backend errors without
claiming acceptance or a source-file preview. Source/finding selection carries a
human label into the shared Jarvis context control. Loaded-source filtering,
pagination and expandable records remain explicit. Project search is embedded
in the supporting left panel.

Models displays definitions that have no version, with engineering question and
scope; exact version context stays unavailable until a version exists. Revision
history sits inside the main dossier. Scoped compact typography keeps guidance
at 11px; principal body text is 12px and headings 15px in the observed layout.

## Executed evidence

`node tests/113-model-dossier.mjs` and
`node tests/114-literature-knowledge.mjs`: PASS.

Real Chromium + FastAPI + Vite, fresh isolated SQLite data, no mocked app routes:

- Registered `Pressure drop handbook` with a citation through the browser.
- Saved a raw claim and a raw datum `1.25 bar`; real API read returned two entries,
  both raw, with the datum value retained.
- Selected the claim, checked its human label in Jarvis, explicitly added it,
  and received a real backend preview: one exact ref, one manifest entry,
  301 estimated tokens. Scrolled the context region to inspect the preview.
- Removed the selection; basket disappeared and composer returned to
  `Send without project context`.
- Reloaded the page and restarted the backend process; saved findings remained.
- Created a real versionless model spec through its API, opened its browser row,
  and verified the engineering question and definition-only state.
- Inspected desktop 1600×1000 and compact 1280×800 screenshots; compact Models
  and Literature had no horizontal document overflow. No page errors occurred.

Scratch reproduction harness: `/workspace/scratch/61bf444950e2/memory-browser.mjs`.
It starts both servers and browser in one process namespace, using backend 8021,
frontend 5191, `JARVISOS_CORS_ORIGINS=http://127.0.0.1:5191`, the scratch venv and
Chromium, and writes screenshots/metrics to the directory below. An initial
harness-only exact label mismatch for the Finding type select was corrected;
final full runs passed.

## Screenshot evidence

Actual PNGs, visually inspected after the scoped typography correction:

- `/workspace/scratch/61bf444950e2/memory-evidence/literature-context-preview.png`
- `/workspace/scratch/61bf444950e2/memory-evidence/literature-source.png`
- `/workspace/scratch/61bf444950e2/memory-evidence/model-definition.png`
- `/workspace/scratch/61bf444950e2/memory-evidence/memory-literature-compact.png`
- `/workspace/scratch/61bf444950e2/memory-evidence/memory-models-compact.png`
- Companion `context-preview.txt`, `after-remove.txt`, and route `*-metrics.json`.

These files are local evidence paths, not published artifacts. Shared Jarvis
context uses an internal scroll region; the preview screenshot deliberately
scrolls it to expose inspected context. This run did not submit an AI message,
verify local model availability, upload files, or exercise model-version creation.
Citation-only records correctly show preview unavailable.
