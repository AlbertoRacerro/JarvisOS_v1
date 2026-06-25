# 1G-B2-F3-C3 — Minimal Local Chat UI

**start_head:** f8d6fe1a4746821a5894012c5abf4c23d165b03c

## Changes

| File | Change |
|---|---|
| `frontend/vite.config.ts` | Added loopback-only dev proxy `/api` → `http://127.0.0.1:8000` |
| `frontend/src/pages/DevLocalChat.tsx` | New dev-only local chat page component |
| `frontend/src/App.tsx` | Added `"devlocalchat"` to `AppPage`; render gated with `import.meta.env.DEV` |
| `frontend/src/components/Layout.tsx` | Added dev-only nav button gated with `import.meta.env.DEV` |
| `frontend/src/styles/global.css` | Added dev local chat styles and dev nav button styles |
| `backend/app/modules/dev_message_route/smoke_adapter.py` | Added `context_filter["assembled_prompt_chars"] = len(prompt)` after prompt assembly |

## C3 Required Corrections — all applied

1. **Vite proxy** — `target: "http://127.0.0.1:8000"`, `changeOrigin: false`, `secure: false`. Host remains `127.0.0.1:5173`. Not exposed over LAN.
2. **`assembled_prompt_chars`** — added at line 398 of `smoke_adapter.py`, after `prompt = assemble_local_chat_prompt(...)`. No authorization gate modified.
3. **Frontend dev gate** — `import.meta.env.DEV` gates both the route render in `App.tsx` and the nav button in `Layout.tsx`. Eliminated from production build by Vite.

## Budget Meter

- Mode: **retrospective** — shown only after a successful `executed=true` response returns `context_filter`.
- Label: **"Last request local prompt budget"** (not model context window).
- Formula: `assembled_prompt_chars / prompt_char_limit * 100`, clamped to `[0, 100]`.
- Empty state until first successful response.
- Warns when `history_turns_omitted_for_prompt_budget > 0` or `history_turns_excluded > 0`.

## response_truncated semantics

- `response_truncated=true` → shows truncation warning.
- `response_truncated=false` → shows "Not sliced by JarvisOS local adapter." (not a completion guarantee).
- `response_truncated_false_semantics: "not_sliced_by_jarvisos_not_completion_guarantee"` respected.

## Tests

- `npm run build` (tsc + vite): PASS — 34 modules
- `pytest test_dev_local_chat.py test_dev_message_route_smoke.py`: 78 passed

## Known Residual Risks

- Dev local-chat remains dev-only and server-env gated.
- The UI does not make local model output production-safe.
- The UI has no persistent memory or retrieval.
- The UI does not implement context refresh/checkpointing.
- Long responses may still be sliced by the local adapter limit.
- The Vite proxy is dev-only and loopback-only.
- The budget meter is retrospective for the last successful request, not live while typing.
