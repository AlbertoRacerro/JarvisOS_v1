# 170 real DWSIM acceptance

`real_dwsim_acceptance.py` runs against an **integrated, frozen candidate** with the scientific PBR evaluator. It uses the FastAPI routes with an isolated temporary `JARVISOS_DATA_ROOT` and the configured real DWSIM 10.2.9 MCP. The script records the exact Git head and MCP digest, creates a synthetic-unqualified 169 set/card, and writes all measured run records and assertions to `JARVISOS_170_EVIDENCE` (default `/tmp/jarvisos-170-real-dwsim.json`). A failed run still writes partial evidence with its error and `complete: false`.

```bash
JARVISOS_DWSIM_MCP_PATH=/absolute/path/to/dwsim-mcp \
JARVISOS_170_EVIDENCE=/absolute/path/170-real-dwsim.json \
backend/.venv/bin/python scripts/qualification/170/real_dwsim_acceptance.py
```

Cases: productive and washout once-through PBR, a changed culture inlet, Mixer → PBR → Separator → Splitter/Heater/Recycle mixed loop with a repeat run, typed oxygen and no-finite-state failures, layout and parameter staleness, pinned set stability after a newer set revision, and explicit card repinning. Assertions compare measured branches, rates, culture and whole-graph balances, owner tags, repeatability and elapsed time. The 107 parameters are clearly labelled synthetic and do not qualify biology.

Before launching, check host CPU/GPU and active DWSIM/backend/browser processes. The script owns only its temporary data root and closes its API client; retain the canonical Jarvis, Agent Relay and local model. The external DWSIM MCP lifetime is managed by the configured backend client. Keep evidence outside the repository until it has been inspected and tied to the final exact head.
