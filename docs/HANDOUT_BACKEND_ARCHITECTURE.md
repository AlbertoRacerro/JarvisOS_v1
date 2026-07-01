# JarvisOS — Handout architettura (backend completo)

Lettore: dev esperto, ignaro del progetto. Obiettivo: capire tutto da zero.

---

## 1. Cos'è JarvisOS

Piattaforma **local-first** che unisce tre cose per il lavoro tecnico privato dell'utente:

1. **Domain Foundation** — knowledge base ingegneristica strutturata (assunzioni, parametri, decisioni, model spec, entità + grafo di link).
2. **Modeling + Runner** — modelli ingegneristici versionati eseguiti come **simulazioni** in sandbox Python locale.
3. **AI layer** — assistente AI con routing semantico locale (+ esterno controllato, pianificato).

Progetto-dominio chiave: **BlueRev** (contenuto proprietario / IP-sensitive). Regola cardine: **niente esce in cloud in silenzio**.

## 2. Principi

- **Local-first**: default su modelli locali (Ollama) e dati locali (SQLite).
- **Fail-closed**: dubbio/errore → percorso sicuro (locale/blocco), mai fallback esterno silenzioso.
- **Blast-radius per il determinismo**: rigore deterministico/gate solo dove l'errore ha raggio alto (egress cloud, esecuzione codice, spesa). Qualità (quale modello, quanto contesto) → fiducia nella semantica, test leggeri.
- **Separazione riga/colonna**: la semantica decide *quanta intelligenza serve* (riga); sicurezza+budget decidono *dove/con-cosa eseguire* (colonna). Una sola semantica per locale ed esterno.
- **PROJECT_CONTEXT = dati, non istruzioni**: il contesto iniettato non può agire da system prompt (difesa prompt-injection esplicita).

## 3. Stack

Python + **FastAPI** (single-process, serve anche il frontend buildato) · **SQLite** (`C:\JarvisOS\jarvisos.db`, con migrazioni versionate) · **Ollama** (localhost:11434) · frontend React/Vite statico · launcher Windows silenzioso (pythonw + `.vbs`, nessun terminale; + stop).

## 4. I quattro sottosistemi

```
┌─────────────────────────────────────────────────────────────────────────┐
│ A. DOMAIN FOUNDATION (knowledge)                                          │
│    workspaces → entities + entity_links (grafo)                           │
│    assumptions · parameters · decisions · model_specs · artifacts · events│
├─────────────────────────────────────────────────────────────────────────┤
│ B. MODELING + RUNNER (simulazione)                                        │
│    model_specs → model_versions → simulation_runs                         │
│    runner_jobs → sandbox Python locale → run_logs / run_artifacts         │
├─────────────────────────────────────────────────────────────────────────┤
│ C. AI LAYER (routing + esecuzione)                                        │
│    gateway → routing (semantico) → execution spine → adapters → ai_jobs   │
│    classificatore locale · RouterPolicy · context builder (retrieval)     │
├─────────────────────────────────────────────────────────────────────────┤
│ D. RUNTIME / INFRA                                                        │
│    Ollama lifecycle · runtime status · resolver localhost · secrets · budget│
└─────────────────────────────────────────────────────────────────────────┘
```

### A. Domain Foundation — knowledge base
Conoscenza di progetto strutturata e tipizzata, per workspace (es. `bluerev`):
- **entities** (generiche, `entity_type`, `raw_payload`) + **entity_links** (grafo: source→target, `link_type`, `confidence`).
- **assumptions** (statement, scope, confidence, status).
- **parameters** (name, symbol, value, unit, source_ref, confidence).
- **decisions** (decision_text, rationale, status, link a run).
- **model_specs** (engineering_question, assumptions/inputs/outputs summary).
- **artifacts** (file: filename, stored_path, sha256, mime).
- **events** (audit log append-only).
- Ogni record ha `maturity_status` (draft→…) e provenienza (`source_ref`).
- Gestita via UI "Domain Foundation"; è l'**unico editor** della knowledge di progetto.

### B. Modeling + Runner — simulazione
- **modeling**: `model_specs → model_versions` (versionati, link ad artifact implementazione) `→ simulation_runs` (input/parameter/output payload, status).
- **runner**: esegue gli script di simulazione in **sandbox Python locale** (`runner_jobs`).
  - Sandbox fail-closed: **niente rete/subprocess** — blocca marker `socket/requests/httpx/urllib/subprocess/os.system`.
  - Caps: timeout (default 10s, max 60s), byte-cap stdout/stderr/output-json/artifact; script **sha256-pinned**; working dir isolata.
  - Output → `run_logs` (stdout/stderr, truncated flag) + `run_artifacts`.
- Scopo: eseguire modelli ingegneristici BlueRev in modo riproducibile e sicuro, senza cloud.

### C. AI layer
Vedi §7–§9 (flow + moduli).

### D. Runtime / infra
- **lifecycle.py**: ciclo vita Ollama (opt-in `JARVISOS_MANAGE_OLLAMA=1`): spawn `ollama serve` se giù → warm qwen3:8b (async) → tree-kill solo se spawnato da JarvisOS.
- **status.py**: read-only `/api/version`, `/api/tags` (installati), `/api/ps` (caricati + spill VRAM).
- **ollama.py**: resolver endpoint **fail-closed localhost-only**.
- **secrets**: storage chiavi API (es. Scaleway) — mai in ledger/log.
- **budget / token_guard / privacy**: budget mensile API, cap token, governance.
- **local_ai_eval**: harness offline di valutazione qualità dei modelli locali (prompt eval, scoring).

## 5. Data model (tabelle SQLite)

```
schema_migrations                     ← versioning schema
workspaces
  ├─ entities ── entity_links         ← knowledge graph
  ├─ assumptions · parameters · decisions
  ├─ model_specs ── model_versions ── simulation_runs
  │                                     ├─ runner_jobs (sandbox exec)
  │                                     ├─ run_logs
  │                                     └─ run_artifacts ── artifacts
  ├─ artifacts (file store, sha256)
  └─ events (audit)
ai_jobs                               ← AI ledger (solo digest)
```

## 6. Retrieval / contesto (ATTUALE + FUTURO)

**Attuale** (`context_builder.py`, `build_workspace_context_bundle`):
- Legge **deterministicamente** le tabelle dominio (decisions, assumptions, parameters) → context blocks, troncati a budget in char (default 32k).
- **NON è retrieval semantico**: nessun vector search, nessun embedding, nessun ranking LLM. È un **full-dump budget-capped** dei record del workspace.
- Output = `ContextBundle` {blocks + digest + source manifest + budget + provenance}. Questa shape è il **seam**: un selettore più intelligente può sostituire il full-dump mantenendo lo stesso contratto.
- Difesa: i blocchi finiscono in `PROJECT_CONTEXT` marcato come **DATI, non istruzioni**.
- In Auto (BRIDGE-1b) il *quando/quanto* è già deciso dalla semantica (`needs_context`, `project_area`, `complexity` → livello none/light/standard/deep, cappato dal toggle utente e dalla capacità del modello). Ma il *cosa* è ancora full-dump.

**Futuro** (RETRIEVAL/DB-1, pianificato):
- Import del **vault Obsidian** (note tecniche strutturate) → DB.
- Selezione **fine di quali fonti** (relevance): la semantica deciderà anche *quali* record, non solo quanto.
- Aperto: vector DB vs retrieval structured/keyword (il contesto è per lo più note tecniche già strutturate → forse structured > vettoriale).

## 7. Hardware e modelli locali

RTX 5070 Ti Laptop, **12 GB VRAM → 1 modello caldo alla volta**.

| route_class | modello Ollama | ruolo |
|---|---|---|
| `local:fast` | `qwen3:8b` | **routing brain** (classifica ~ogni richiesta) + risposte semplici, sempre caldo |
| `local:general` | `gemma4:12b-it-qat` | reasoning generale |
| `local:coder` | `deepseek-coder-v2:16b` | coding |
| `local:coder_heavy` | `qwen3-coder:30b` | coding pesante (sfora 12 GB, lento) |
| `local:fake` | deterministico | test / back-compat |
| `external:cheap` | Scaleway | unico esterno oggi, **solo manuale** |

## 8. Flusso richiesta AI

```
HTTP POST /ai/tasks/run  (FastAPI) ── prompt, route_class, task_kind, include_project_context, max_tokens
        │
        ▼
AIGateway.run_task ── route_class ?
   ├─ None ─────────────────► local:fake
   ├─ "local:*"/"external:*" (MANUALE) ─► [context se richiesto] ─► run_ai_task  (bypassa bridge)
   └─ "auto" ─► RouterPolicy Bridge
                    │
                    ▼
     classify_text (qwen3:8b /api/chat)      [FAIL-CLOSED: source = model | deterministic | fallback]
                    │  → {task_type, project_area(bluerev/…), complexity, needs_context, sensitivity_hint, confidence}
                    ▼
     capability_from_classification  ── ROW (provider-agnostica): simple|general_reasoning|coding|heavy_coding|deep_reasoning
                    │
      ┌─────────────┼──────────────────────────┬──────────────────────────┐
      ▼             ▼                          ▼                          ▼
 control state?   capability→route locale     context_decision           sensitivity→RouterPolicyInput
 (ambiguous→clar; (matrix, COLONNA=locale)    (needs_context+project_area (mappa onesta; tier ESTERNI
  unsafe→blocked;                              +complexity→level; cap:      BLOCCATI deterministicamente)
  external_api→                                toggle utente + capacità
  proposed_external)                           modello)
      │                                                                    │
      ▼                                                                    ▼
 non-exec outcome                                    RouterPolicy producer (decision.py, canonico)
 (no run, ledger, no provider)                       → {route_tier, route_action, permissions}
                                                                    │
                                                                    ▼
                                        _is_auto_local_safe(decision)?
                                        (answer_local/route_local ∧ LOCAL_FAST/LOCAL_ONLY
                                         ∧ no external target ∧ provider/network/tool/state=False)
                                          ├─ no ─► control outcome (no esecuzione)
                                          └─ yes ─►
                                                  ▼
                             [se level≠none] context_builder → PROJECT_CONTEXT (workspace)
                                                  ▼
                             run_ai_task (spine): route_class → ProviderBinding → adapter
                                                  ▼
                             LocalOllamaAdapter → Ollama /api/generate → modello locale
                                                  ▼
                             AIResponse ─► ledger (ai_jobs, digest) ─► HTTP response
```

RouterPolicy producer = motore a **regole first-match** deterministico. Tier: `LOCAL_ONLY(0)<LOCAL_FAST(1)<CHEAP_EXTERNAL(2)<SCIENTIFIC_MEDIUM(3)<FRONTIER(4)` + control (USER_CONFIRM, BLOCKED). In Auto è usato come **gate di permesso locale**, non selettore di modello.

## 9. Moduli backend (mappa)

| Modulo | Ruolo |
|---|---|
| `app/main.py` | FastAPI app, lifespan, mount frontend statico |
| `api/{health,system,dev_message_route}` | health/status + endpoint dev router-policy smoke |
| **AI** | |
| `ai/gateway.py` | `run_task`: branch route_class |
| `ai/routing/bridge.py` | Auto: classify→capability→matrix→context→gate→run |
| `ai/routing/capability_route_matrix.py` | ROW→route locale + budget contesto per (route,level) |
| `ai/routing/decision.py` | RouterPolicy producer canonico (fail-closed) |
| `ai/routing/{invariants,safe_local}.py` | invarianti runtime + predicato local-safe |
| `ai/execution.py` | spine `run_ai_task`: binding→adapter→ledger |
| `ai/providers/*` | LocalOllama, Fake, Scaleway, DeepSeek adapter |
| `ai/context_builder.py` | assembly prompt + retrieval workspace (full-dump budget) |
| `ai/{budget,token_guard,privacy,settings}.py` | governance token/costo/privacy |
| **Local AI** | |
| `local_ai/classification/` | classificatore semantico qwen3:8b (/api/chat), tipizzato fail-closed |
| `local_ai/intake/` | segnali deterministici pre-classificazione |
| `local_ai/runtime/{lifecycle,status,ollama}.py` | ciclo vita / stato / resolver Ollama |
| `local_ai_eval/` | harness valutazione qualità modelli locali (offline) |
| **Dominio** | |
| `workspaces/` | CRUD workspace + knowledge records |
| `modeling/` | model_specs / versions / simulation_runs |
| `engineering/` | entità/analisi ingegneristiche (parte Domain Foundation) |
| `runner/` | **sandbox Python** (safety: no rete/subprocess, caps, sha256) |
| `files/` | artifact/file registry (sha256) |
| `secrets/` | storage chiavi API |
| `events/` | audit log |
| **Framework** | |
| `tools/`, `agents/` | registry minimali (skeleton per orchestrazione/multi-agent futura) |
| `core/{database,schema,paths,config}.py` | SQLite, schema+migrazioni, path, config |

## 10. Modello di sicurezza

- **Egress cloud**: bloccato deterministicamente in Auto (`blocked_provider_tiers`); mai per fiducia nel classificatore.
- **Sensitivity** (Auto local-only): public/internal/unknown→risposta locale; confidential/sensitive_ip→risposta **locale** (LOCAL_ONLY); secret→blocked; external_api_request→`proposed_external` (non eseguito).
- **Runner sandbox**: no rete/subprocess, timeouts, byte-cap, script sha256-pinned.
- **Prompt-injection**: PROJECT_CONTEXT = dati, non istruzioni.
- **Ledger** (`ai_jobs`): solo digest sha256 (route, provider, model, prompt/context/output digest, token, latency, error). Mai contenuto/segreti in chiaro.
- **Resolver Ollama**: localhost-only, fail-closed (http, 127.0.0.1/localhost/::1, no query/frag/cred).

## 11. Stato attuale (implementato + validato su Ollama reale)

```
DOMINIO  : workspaces/entities/assumptions/parameters/decisions/model_specs (schema + CRUD)
MODELING : model_specs/versions/simulation_runs + runner sandbox
AI LOCALE: model routing → runtime status → resolver → default → lifecycle → launcher desktop
ROUTER   : producer canonico → baseline → BRIDGE-1a (Auto→locale by task_kind)
           → BRIDGE-1b (Auto SEMANTICO: classify→capability→matrix locale + contesto)
UI       : AI Console (Auto/task_kind, mostra route+modello), Domain Foundation, Diagnostics
SMOKE    : Auto verificato end-to-end su Ollama reale, ledger scritto
```
**Fix in corso (BRIDGE-1b-R2):** contenuto sensibile `LOCAL_ONLY/propose_only` non eseguito → eseguirlo in locale (locale=sicuro), test su tutto lo spettro sensitivity.

## 12. Architettura pianificata (non implementata) — ordine per blast-radius

1. **BRIDGE-1b-R2** — esegui sensibile in locale *(in corso)*.
2. **LOCAL-REWARM-1** — re-warm qwen3:8b dopo task non-8b (su 12 GB i coder sfrattano il brain).
3. **SENSITIVITY-HARDEN-1** — detector privato/IP **italiano/BlueRev**, frase/intenzione (es. "parametri proprietari", "dati non pubblici"), non nomi nudi. Precondizione a qualsiasi esterno.
4. **REDACTION-1** — redazione **deterministica, fail-closed** del sensibile prima dell'egress. Blast-radius massimo (miss = fuga IP irreversibile). Mai LLM per redigere la propria fuga.
5. **EXTERNAL-REGISTRY-1 + matrice power-sensitivity** — provider esterni (deepseek v4, glm 5.2, kimi k2.7, gpt-5-mini, sonnet 5, gemini 3 pro, opus 4.8) con capacità/costo **+ attributo hosting (EU-only)**. Riempie le **colonne esterne** delle stesse righe di capacità (nessun secondo layer semantico).
6. **EXTERNAL-EXECUTE + CONFIRM** — se `capability_exceeds_local` ∧ sensibile: redigi → provider EU → **conferma umana (mostra payload redatto)** → esegui. Schema RouterPolicy ha già `redaction_required`/`redaction_status`.
7. **RETRIEVAL/DB-1** — import vault Obsidian → selezione *quali* fonti (oggi solo quando+quanto). Vector DB vs structured (aperto).
8. **TOOLS/AGENTS orchestration** — oggi solo registry skeleton; futuro: agenti/tool per task multi-step (autopilot + gate umano).
9. **LOCAL-RUNTIME-DISTRIBUTED** — qwen3:8b (brain) su nodo LAN dedicato (≥8 GB) → libera i 12 GB dell'Helios. Richiede resolver → **allowlist di endpoint locali fidati** (localhost + host LAN esplicito), sempre fail-closed vs cloud.
10. **Osservabilità** — i job Auto eseguiti loggano la route risolta, non l'origine "auto" né la decision_reason → aggiungere provenienza.

### Estensione esterna (pianificata)
```
capability_exceeds_local (deep_reasoning) ∧ sensibile
   → SENSITIVITY-HARDEN (detector IT/BlueRev)   ── se non-redigibile → resta locale/blocca
   → REDACTION (deterministica, fail-closed)     → payload redatto + redaction_status
   → EXTERNAL registry (EU-hosted, capacità≥riga, budget)
   → CONFIRM umano (payload redatto + provider + costo)  [nuova decisione, consent_context]
   → external adapter → provider EU → risposta → ledger
```

## 13. Domande aperte per un secondo parere

- **Redazione** deterministica affidabile su IP tecnico (parametri/correlazioni) senza semantica: fattibile, o serve un modello locale dedicato + validazione deterministica a valle?
- **Tetto locale** (`capability_exceeds_local`): come definirlo in modo non arbitrario (quando un task supera davvero i modelli locali)?
- **Retrieval**: vector DB vs structured su vault Obsidian, dato che il contesto è per lo più note tecniche strutturate.
- **Nodo LAN vs upgrade GPU singola**: trade-off latenza routing vs semplicità.
- **Runner**: estendere la sandbox oltre Python (altri linguaggi/tool) mantenendo il no-network?
- **Determinismo vs semantica**: dove il progetto sta iper-blindando cose a basso raggio (overengineering) vs dove manca rigore su cose ad alto raggio.

## 14. Direzioni prioritarie (nota per il collaboratore)

Due direzioni che l'autore vuole spingere. Non sono "forse un giorno": sono obiettivi voluti, gated solo dalla sicurezza.

### A. Collegare l'esterno appena la sicurezza è accettabile
- **Stato oggi**: l'esterno è **murato fuori da Auto** by design (§8, §10). L'unico modo di uscire dal locale è selezionare a mano `external:cheap`; nessuna logica dietro. Il retrieval è **sempre e solo locale** (§6): full-dump SQLite, zero rete, mai una chiamata esterna per recuperare contesto.
- **Obiettivo voluto**: questo local-only è una **tappa, non lo stato finale**. Appena la porta di sicurezza è affidabile, si collega l'esterno al flusso Auto — è tra le cose che l'autore vuole *di più* (routing semantico che smista anche verso provider esterni).
- **Cosa significa "sicurezza accettabile"** (la barra, alta perché il raggio è massimo = fuga IP irreversibile):
  1. **SENSITIVITY-HARDEN** — detector IT/BlueRev affidabile (frase/intenzione, non nomi nudi).
  2. **REDACTION deterministica fail-closed** — garantisce che nulla di sensibile-non-redatto esca; mai l'LLM a redigere sé stesso.
  3. **CONFIRM umano** — l'utente vede il payload redatto + provider + costo prima dell'invio.
  Superati questi tre, l'esterno si aggancia alle **colonne esterne** della matrice già esistente (§7), con vincolo **provider EU-hosted**. Nessun secondo layer semantico: stessa classificazione, colonna diversa.
- **Priorità pratica**: collegarlo *il prima possibile* una volta passata la barra, non appesantire l'attesa con feature non necessarie.

### B. Retrieval vettoriale / Obsidian-style, su reference di giganti
- **Stato oggi**: retrieval = full-dump deterministico (§6). Il seam (`ContextBundle`) è già pronto ad accogliere un selettore più intelligente senza toccare il resto.
- **Obiettivo voluto**: retrieval **vero** che sceglie *quali* fonti — vettoriale (embedding + similarity) e/o **structured tipo Obsidian** (grafo di link/backlink). Sorgente: **vault Obsidian** dell'autore (note tecniche già strutturate e linkate → un grafo semantico quasi pronto).
- **Metodologia richiesta — "reference di giganti"**: NON reinventare. Il progetto ha già questo pattern per il routing (**reference audit** di RouteLLM/Wayfinder — vedi `docs/reference_audits/`, commit `d1ff849`). Stessa cosa per il retrieval: studiare architetture consolidate e adattarle al vincolo local-first + fail-closed. Reference candidate da valutare:
  - pattern RAG maturi (LlamaIndex / LangChain retrieval, query routing, reranking);
  - vector store locali (pgvector / LanceDB / Chroma / sqlite-vec) — coerenti col local-first;
  - il **modello grafo di Obsidian** (link/backlink) come struttura di retrieval nativa, potenzialmente più adatto di embedding puri dato che il contenuto è già strutturato e linkato;
  - embedding locali (es. via Ollama) per restare offline.
- **Aperto (dove il collaboratore può incidere)**: vettoriale vs structured/grafo per contenuto già-strutturato; come far convergere i due (hybrid); come il retrieval alimenta anche il ramo esterno (contesto redatto → provider EU) senza aprire falle.
```

