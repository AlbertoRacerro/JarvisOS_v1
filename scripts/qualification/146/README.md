# HERMES-RUNTIME-1 qualification

`hermes_smoke.py` runs the pinned Hermes 0.21.4 worker behind the Jarvis supervisor, loopback inference relay, and read-only Jarvis MCP capability broker. It records its result in `hermes-smoke.json`.

The recorded inference source is a deterministic loopback stub. This qualifies worker transport, broker routing, event projection, interrupt handling, and process recovery; it is not evidence of local model quality or a Windows/WSL deployment.

Windows Ollama reported `qwen3:8b` installed through `powershell.exe`. The Jarvis adapter resolves Ollama to `127.0.0.1:11434` and the WSL loopback probe was refused. Jarvis's existing Ollama endpoint validator accepts loopback hosts only, so substituting the WSL host IP would bypass that boundary; the accepted smoke therefore used the deterministic relay stub.

Native Hermes delegation and skills remain disabled. Their current actions are not individually routed through the Jarvis capability broker, so they are not exposed to the worker until that boundary exists. Hermes memory and session search remain worker-local and have no canonical Jarvis write authority.

Run with the pinned Hermes checkout installed in a separate environment:

```bash
JARVIS_HERMES_VENV=/path/to/hermes-venv backend/.venv/bin/python scripts/qualification/146/hermes_smoke.py
```
