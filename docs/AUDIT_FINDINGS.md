# JarvisOS — Audit Findings Log

Registro durevole dell'audit severo del backend. Aggiornato man mano, modulo per
modulo. Gravità: 🔴 critico · 🟠 alto · 🟡 medio · 🔵 basso/cosmetico.

Stato: `proposto` (trovato, non ancora deciso) · `da-fixare` (concordato) ·
`fatto` · `rimandato` · `non-è-un-bug`.

Contesto di rischio concordato: **locale oggi** (backend in ascolto solo su
`127.0.0.1:8000`, vedi `scripts/start-backend.ps1:35`), ma la sicurezza è
valutata **come se in futuro fosse esposto** in rete / multi-utente.

Baseline test all'avvio dell'audit: **324 passed in ~18s**, completamente
offline (provider `fake`, nessun costo).

---

## Tier 0 — Confine del sistema (esposizione)

### T0-1 🟠 Nessuna autenticazione su nessun endpoint — `rimandato`
- **Dove:** tutti i router montati in `backend/app/main.py:33-39`; nessuna
  dipendenza di auth in nessuna route.
- **Oggi:** binding su `127.0.0.1` → solo la tua macchina → rischio basso.
- **Se esposto:** chiunque raggiunga la porta 8000 può creare/leggere
  workspace e dati, **salvare/cancellare la chiave API Scaleway**
  (`POST/DELETE /secrets/scaleway/api-key`) e **lanciare l'esecuzione di codice**
  (`POST /runner-jobs/{id}/run`).
- **Perché conta:** a runtime non esiste alcun concetto di utente/permesso,
  mentre i doc parlano di RBAC e quarantena IP → drift docs/codice; e nel
  momento in cui il binding diventasse `0.0.0.0` non c'è alcuna barriera.
- **Fix proposto:** rendere il binding loopback un **invariante esplicito e
  documentato**; prima di qualsiasi esposizione, gate con token statico in
  header (`X-JarvisOS-Token`) come confine minimo. RBAC completo rimandabile.

### T0-2 🟡 CORS `allow_credentials=True` inutile — `rimandato`
- **Dove:** `backend/app/main.py:25-31`.
- **Problema:** l'app non usa cookie/sessioni (non c'è auth), quindi
  `allow_credentials=True` non serve. Con `allow_headers=["*"]`. Non sfruttabile
  ora (origini esplicite localhost), ma è una configurazione lasca latente.
- **Fix proposto:** `allow_credentials=False`; mantenere le origini esplicite
  (mai `*` con credenziali).

### T0-3 🟡 `/system/info` espone dettagli interni senza auth — `rimandato`
- **Dove:** `backend/app/api/system.py:13-70`.
- **Problema:** restituisce path assoluti del filesystem (`data_root`, file DB),
  budget/spesa AI, cap token, configurazione provider. Non restituisce la chiave
  (corretto), ma se esposto è ricognizione utile a un attaccante.
- **Fix proposto:** legare allo stesso confine di auth di T0-1; eventualmente
  ridurre i campi. Basso ora.

---

## Tier 1 — Esecuzione codice e integrità dati

### T1-0 ✅ Reassurance: il runner NON esegue codice arbitrario oggi
- `create_model_implementation` (`runner/service.py:60-63`) **copia sempre** il
  file fisso `examples/batch_growth.py`; `ModelImplementationCreate` non ha alcun
  campo per fornire uno script. Quindi oggi il runner può eseguire **solo** lo
  script di esempio revisionato, mai codice utente o generato da AI. Tutta la
  macchina di hash/blocklist/validazione path è difesa-in-profondità per un uso
  futuro che oggi non esiste. È un bene; lo annoto per chiarezza.

### T1-1 🟠 Race / non-idempotenza in `run_runner_job` — `fatto`
> FIX: claim atomico `_claim_and_mark_running` (UPDATE ... WHERE status='queued',
> rowcount==1). Test `test_runner_job_atomic_claim_runs_only_once`.
- **Dove:** `runner/service.py:255-287`. Il check `status != "queued"` (conn A,
  righe 256-263) e la transizione a `running` (`_mark_running`, conn B, riga 287)
  avvengono in **transazioni separate** senza lock tenuto in mezzo (TOCTOU).
- **Cosa si rompe:** due `POST /runner-jobs/{id}/run` paralleli sullo stesso job
  passano entrambi il check ed **eseguono il subprocess due volte**, scrivendo
  log e artifact doppi e corrompendo lo stato del run. Gli endpoint sync girano
  in threadpool → concorrenza reale.
- **Fix proposto:** claim atomico —
  `UPDATE runner_jobs SET status='running',... WHERE id=? AND status='queued'`
  e procedere solo se `rowcount == 1` (singola istruzione = atomica in SQLite).

### T1-2 🟡 Operazioni multi-step non atomiche — `proposto`
- **Dove:** `create_model_implementation` (`runner/service.py:44-121`) valida in
  una connessione, fa `mkdir`+`shutil.copy2` su filesystem, poi inserisce in una
  **seconda** connessione. Un crash a metà lascia file orfani senza record DB (o
  viceversa). Il ciclo di vita del run sparpaglia gli aggiornamenti di stato su
  molte transazioni separate.
- **Cosa si rompe:** stato incoerente su crash; nessuna garanzia "tutto-o-niente".
- **Fix proposto:** raggruppare le scritture correlate in una sola transazione
  dove possibile; inserire il record DB prima/insieme alla copia file.

### T1-3 🟡 Nessun recupero per job bloccati in `running` — `proposto`
- **Dove:** `run_runner_job` accetta solo `queued`; se il server muore durante
  `execute_python_script`, job e simulation_run restano `running` per sempre,
  non rieseguibili.
- **Fix proposto:** reaper all'avvio che marca i `running` orfani come
  `failed`/`interrupted`, oppure permettere il re-queue.

### T1-4 🟠 SQLite senza `busy_timeout` né WAL — `fatto`
> FIX: `PRAGMA busy_timeout=5000` + `journal_mode=WAL` in `open_sqlite_connection`.
- **Dove:** `core/database.py:43-53`. Connessione nuova per chiamata, journal
  mode di default, `busy_timeout` = 0.
- **Cosa si rompe:** con due scrittori concorrenti il secondo riceve subito
  `database is locked`. Raro single-user, problema reale se esposto/multi-utente.
  Aggravato dalle operazioni che aprono più connessioni.
- **Fix proposto:** `PRAGMA busy_timeout=5000` (e valutare `journal_mode=WAL`)
  in `open_sqlite_connection`. Vittoria facile e sicura.

### T1-5 🔵 Blocklist marker fragile (falsi positivi + aggirabile) — `proposto`
- **Dove:** `runner/safety.py:18-49`, `preflight_script_policy:198-203`.
  Match di sottostringa su testo minuscolizzato: aggirabile (`__import__`,
  `getattr`, encoding) e con falsi positivi su codice scientifico legittimo
  (variabile `token`, commento con "password"). Oggi inerte (vedi T1-0).
- **Fix proposto:** se in futuro si accettano script utente, sostituire con
  analisi AST + allowlist di import, non blocklist di stringhe. Per ora: nota.

### T1-6 🔵 Possibile `OverflowError` su input estremi nel modello — `proposto`
- **Dove:** `examples/batch_growth.py:59`. `exp(mu_max*dt)` con `mu_max` molto
  grande supera il limite float → `OverflowError`. La validazione limita il
  numero di passi (`t_final/dt ≤ 10000`) ma non la magnitudine di `mu_max`.
- **Cosa si rompe:** il run fallisce in modo gestito (process exit ≠ 0,
  catturato), nessun crash del server. Solo robustezza.
- **Fix proposto:** limite ragionevole su `mu_max` o gestione esplicita
  dell'overflow con warning.

### T1-7 🔵 Dominio: modello esponenziale non rappresentativo di un PBR — info
- `examples/batch_growth.py`: crescita di Malthus pura (nessun carico massimo,
  luce, nutrienti). Corretto come smoke test; da sostituire con cinetica reale
  (Monod/logistica, self-shading) quando inizia BlueRev. Non è un bug.

---

## Tier 2 — Gate di policy AI e secrets

### T2-0 ✅ Reassurance: i segreti non trapelano + live spento di default
- La chiave non è mai restituita grezza (`_masked_preview` la maschera), mai
  scritta negli eventi (motore di redazione in `events/service.py:100-127`),
  mai salvata in `ai_settings`. I test `test_scaleway_secrets.py` lo verificano.
- Il percorso live richiede molti flag tutti OFF di default
  (`paid_ai_enabled`, `scaleway_live_smoke_test_enabled`, chiave presente, ecc.).
- Il gateway principale `create_modeling_draft` esegue **solo** il provider
  `fake`; le chiamate live esistono solo nei percorsi smoke ristretti.

### T2-1 🟠 Il budget in dollari NON viene mai incrementato (controllo inerte) — `proposto`
- **Dove:** `record_scaleway_token_usage` (`ai/settings.py:131-144`) aggiorna solo
  i token, non la spesa. `update_ai_settings` (`ai/settings.py:96-105`) **non
  include `api_spend_month_to_date_usd` nella clausola SET**. `ensure_ai_settings`
  lo inizializza a 0.
- **Cosa si rompe:** `api_spend_month_to_date_usd` resta **permanentemente 0**,
  quindi la condizione `api_spend >= monthly_api_budget_usd` (`ai/budget.py:38,60`)
  non scatta mai. Il "budget mensile in dollari" appare in `/ai/status` e
  `/system/info` come se proteggesse, ma è **inerte**. L'unico controllo di costo
  reale sono i **token cap** (questi sì funzionano).
- **Rischio mentale:** "ho impostato 5$ di budget" → falsa sicurezza; ti protegge
  solo il token cap.
- **Fix proposto:** o (a) incrementare la spesa stimata (token×prezzo) in
  `record_scaleway_token_usage` e applicarla nel gate, oppure (b) rimuovere il
  budget in dollari dall'UI/stato e dichiarare i token cap come unico controllo.
  Scegliere una sola storia per evitare il controllo-fantasma.

### T2-2 🟠 (se esposto) I contatori d'uso e i cap sono azzerabili via PUT non autenticato — `proposto`
- **Dove:** `AISettingsUpdate` (`ai/models.py:21-22,19-20`) espone
  `scaleway_input/output_tokens_month_to_date` e i `*_token_cap` come scrivibili;
  `update_ai_settings` li scrive da input utente.
- **Cosa si rompe:** via `PUT /ai/settings` (senza auth, vedi T0-1) si possono
  azzerare i contatori d'uso e alzare i cap → **bypass dell'unico controllo di
  costo funzionante**. Locale è una tua manopola (ok); esposto è una falla.
- **Fix proposto:** togliere i contatori d'uso dai campi scrivibili dell'update
  (l'uso lo scrive solo il sistema dopo una chiamata); separare "config" da
  "contatori runtime".

### T2-3 🟡 In FAST_DEV (modalità di DEFAULT) i contenuti confidential/IP non sono bloccati — `rimandato (scelta deliberata)`
> NOTA: `tests/test_ai_fast_dev_policy.py:13` asserisce *di proposito* che FAST_DEV
> ammetta testo con "patent... for BlueRev" → è un tradeoff scelto per velocità di
> sviluppo, non una svista. Da chiudere quando si accende il percorso esterno
> (default fail-safe), e il classificatore semantico arriva con la AI evaluation.
> Non modificato in questa sessione per non ribaltare comportamento intenzionale.
- **Dove:** `privacy.py:144-145`. Nel ramo `FAST_DEV` la funzione ritorna
  `external_allowed=True` per tutto ciò che non è un segreto strutturale; i
  controlli `sensitive_ip`/`confidential`/`bluerev` (righe 149-152) stanno **dopo**
  il `return` e vengono saltati.
- **Cosa si rompe:** un prompt come "bluerev proprietary geometry" in FAST_DEV
  (default da `ensure_ai_settings`) sarebbe ammesso all'esterno. Contraddice il
  doc architetturale ("sensitivity rules pass"). Oggi contenuto perché il live è
  spento di default e il prompt è limitato a 500 char, ma il default è permissivo.
- **Fix proposto:** applicare i controlli sensitive_ip/confidential **anche** in
  FAST_DEV, o non usare FAST_DEV come default quando il live è abilitabile.

### T2-4 🟡 Logica di gate duplicata (rischio drift) — `proposto`
- **Dove:** `ai/budget.py` — `evaluate_ai_status` (riga 15) e
  `evaluate_live_scaleway_smoke_gate` (riga 99) reimplementano quasi la stessa
  sequenza di controlli con ordini diversi. Aggiornarne uno e non l'altro crea
  incoerenze tra ciò che `/status` dichiara e ciò che il percorso live applica.
- **Fix proposto:** estrarre un'unica funzione di valutazione dei gate condivisa.

### T2-5 🔵 Stima token `len/4` grezza — `proposto`
- **Dove:** `token_guard.py:14-15`. Sottostima per testo non inglese/codice;
  la chiamata può sforare di poco il cap (corretto poi dai token riportati).
  Minore.

### T2-6 🟡 La variabile d'ambiente mette in ombra silenziosamente la chiave da app — `proposto`
- **Dove:** `secrets/storage.py:33-44`. Se `SCALEWAY_API_KEY` è impostata,
  la chiave salvata da app viene ignorata. Il campo `source` lo segnala
  ("env"), ma può confondere. Basso.

### T2-7 🔵 Chiave in chiaro via HTTP + solo in memoria — `proposto`
- **Dove:** `secrets/routes.py:18-34`, `secrets/storage.py`. Accettato dai doc
  (store DPAPI rimandato). Per scenario esposto: POST in chiaro. Basso (locale).

---

## Tier 3 — Dominio, CRUD e correttezza

### T3-0 ✅ Reassurance: gestione errori coerente
- `modeling/routes.py:34-39` mappa `ValueError`→404, `IntegrityError`→400, altro→500;
  `workspaces/routes.py:15-16` mappa slug duplicato→409. Errori prevedibili,
  niente 500 sui casi attesi, nessuno stack trace al client (FastAPI non è in debug).

### T3-1 🟡 `parameters.value` è TEXT senza validazione numerica/unità — `proposto`
- **Dove:** `core/schema.py:146`, `modeling/service.py:create_parameter`.
- **Problema:** per una futura libreria di parametri BlueRev (nome, valore, unità,
  intervallo, fonte) il valore è testo libero non validato: nessun controllo
  numerico, di unità o di range. Rilevante per il tuo obiettivo. Da rinforzare
  quando inizia il workbench. Non è un bug oggi (tabella poco usata).

### T3-2 🔵 Nessun UPDATE/DELETE nel dominio — info
- Solo create/list/get. Coerente con il V0 "append-only/minimo", ma non puoi
  correggere uno spec o un parametro. Limitazione nota, non bug.

### T3-3 🔵 Creazione di entity/artifact senza event log — `proposto`
- `engineering/service.py` e `files/service.py` non registrano eventi e non
  validano il workspace, a differenza di tutto il resto (lacuna nell'audit
  trail). Vedi T4-1: questi moduli oggi non sono nemmeno montati.

---

## Tier 4 — Architettura e drift docs/codice

### T4-1 🟡 Moduli `engineering` e `files` sono codice morto/non collegato — `proposto`
- **Dove:** `engineering/routes.py` non è incluso in `main.py:33-39`; `files` non
  ha route; nessuno dei due è chiamato dal runtime o coperto da test.
- **Problema:** ~4 file di codice non raggiungibile che per giunta non validano
  il workspace né loggano eventi. Se collegati in futuro così come sono,
  ereditano queste lacune.
- **Fix proposto:** o rimuoverli, o collegarli allineandoli al pattern del resto
  (validazione workspace + event log).

### T4-2 ℹ️ ~57% del sorgente è l'harness offline `local_ai`/`local_ai_eval`
- **Dato:** ~9.988 righe su 24 file, **non importate** da `main`/`api`/route.
  È scaffolding di ricerca/valutazione Gemma lanciato a mano. Il backend in
  esecuzione è ~7,4k righe. Non è un bug; serve a inquadrare dove sta il rischio
  (concentrato nel runtime piccolo) e la superficie di manutenzione.

### T4-3 🟡 Logica di gate AI duplicata — vedi T2-4
- Estrarre un'unica funzione condivisa per evitare divergenze tra `/status` e il
  percorso live.

### T4-4 🟡 Drift docs/codice su controlli "di sicurezza" — `proposto`
- I doc presentano budget in $ (T2-1) e regole di sensibilità (T2-3) come attivi,
  ma il runtime li ha inerti/permissivi nel default. Molti altri doc sono
  onestamente etichettati "future/conceptual" (bene). Allineare le poche
  affermazioni che descrivono come "attivo" ciò che non lo è.

---

## Tier 5 — Igiene di config, dipendenze, logging

### T5-1 🟠 Manca un linter/type-checker (rete di sicurezza assente) — `fatto`
> FIX: aggiunto `backend/pyproject.toml` con config `ruff` (E/F/I/B/UP) e `mypy`
> (runtime backend, esclude harness `local_ai*`), + `pytest` testpaths.
> `ruff check app tests` → pulito (55 auto-fix applicati). `mypy app` → da 12 a 7
> errori: risolti i strutturali (`log_event` payload → `Mapping`; firma
> `save_scaleway_api_key(str | None)`) + bonus robustezza runner (artifacts non-lista
> ora solleva errore pulito invece di possibile `TypeError`). I 7 residui sono
> `int(object)` benigni e guardati nei percorsi diagnostici provider — baseline
> nota da ripulire in modo incrementale.
- **Problema:** nessun `ruff`/`mypy`/formatter configurato. Per chi sta imparando
  è la leva preventiva più alta: `mypy` avrebbe segnalato a colpo classi di bug
  come questo audit (es. campi mancanti negli UPDATE, tipi incoerenti).
- **Fix proposto:** aggiungere `ruff` + `mypy` (e un `requirements-dev.txt`),
  con una config minima; opzionale pre-commit. Vittoria enorme nel tempo.

### T5-2 🟡 `requirements.txt` non blocca `pydantic` — `fatto`
> FIX: pinnato `pydantic==2.13.4`; create `requirements-dev.txt` (pytest/ruff/mypy)
> separate dalle dipendenze di runtime.
- **Dove:** `backend/requirements.txt`. `pydantic` (dipendenza centrale) arriva
  solo di rimbalzo da FastAPI; una futura risoluzione diversa può rompere i
  modelli. Inoltre dev-deps (`pytest`) mischiate al runtime.
- **Fix proposto:** pinnare `pydantic` esplicitamente; separare le dev-deps.

### T5-3 🔵 Logging basilare — info
- `core/logging.py` usa `basicConfig(INFO)`; non logga payload. Gli access log di
  uvicorn registrano i path ma i segreti viaggiano nel body POST (non loggati).
  OK; nessuna azione necessaria ora.

---

## Riepilogo per gravità (snapshot)

- 🟠 Alti: T1-1 (race runner), T1-4 (db lock), T2-1 (budget $ inerte),
  T2-2 (cap azzerabili se esposto), T5-1 (no linter/type-checker),
  + T0-1 (no auth, conta se esposto).
- 🟡 Medi: T1-2, T1-3, T2-3, T2-4/T4-3, T2-6, T3-1, T4-1, T4-4, T5-2,
  + T0-2, T0-3.
- 🔵 Bassi/cosmetici/info: T1-5, T1-6, T1-7, T2-5, T2-7, T3-2, T3-3, T4-2, T5-3.

Reassurance confermate: runner non esegue codice arbitrario (T1-0); segreti non
trapelano e live spento di default (T2-0); errori di dominio gestiti bene (T3-0).

---

## Sequenziamento secondo la roadmap dell'utente

Roadmap dichiarata: (1) finire AI evaluation → (2) connessione AI esterne +
chat + salvataggio memoria automatico (prima bozza usabile) → (3) passata di
hardening pre-UI. L'audit è organizzato per servire questo piano.

### A) Fai ORA (a prescindere — aiuta il codice che stai per scrivere)
- **T5-1** — `ruff` + `mypy` + `requirements-dev.txt`. Rete di sicurezza sul
  codice nuovo dell'integrazione esterna, mentre lo scrivi.
- **T5-2** — pinnare `pydantic` (banale; evita sorprese durante il lavoro su
  provider/dipendenze).

### B) Costruisci BENE dentro la feature "AI esterne + memoria" (non dopo)
- **T2-1 / T2-2** — freno di costo reale: o budget in $ funzionante, o token cap
  dichiarato unico controllo + contatori non azzerabili dall'update. Da definire
  *mentre* si collega il provider esterno, non dopo.
- **T2-3** — default di privacy a prova di errore (blocca esterno salvo contenuto
  marcato pubblico). Il classificatore intelligente (Gemma) resta legato alla AI
  evaluation; il default sicuro è una riga, da mettere quando si accende il live.
- **T2-4 / T4-3** — unificare la logica dei gate mentre la si tocca comunque.
- **T1-4** — `busy_timeout` può accompagnare il lavoro su memoria (scritture
  concorrenti chat + auto-save).

### C) Rimanda alla passata di hardening pre-UI (deferire è OK)
- **T0-1** auth, **T0-2** CORS, **T0-3** system info.
- **T1-2/T1-3** atomicità/reaper, **T1-5/T1-6** runner.
- **T2-6/T2-7** secrets (env shadow, plaintext/in-memory).
- **T3-1** validazione parametri (quando inizia il workbench BlueRev).
- **T4-1** rimozione/collegamento dead code (engineering/files).
- **T4-4** allineamento doc/codice (dopo aver sistemato B).

---

## Stato fix (sessione audit 2026-06-23)

Verifica finale: **325 test passano · `ruff check app tests` pulito · `mypy app`
7 errori benigni residui**.

### Fatti
- **T1-1** claim atomico runner (+ test).
- **T1-4** `busy_timeout` + WAL.
- **T5-1** setup `ruff` + `mypy` (pyproject.toml) + fix strutturali mypy + bonus
  robustezza runner (artifacts non-lista).
- **T5-2** pin `pydantic` + `requirements-dev.txt`.

### NON fatti di proposito (giudizio, non pigrizia)
- **T2-1 / T2-2 (budget)** — serve una tua decisione di prodotto (budget $ reale
  vs solo token cap) e tocca i test; non li tocco alla cieca.
- **T2-3 (privacy FAST_DEV)** — comportamento deliberato + da te rimandato; il fix
  vero dipende dalla AI evaluation. Da chiudere quando accendi l'esterno.
- **T2-4 (unificazione gate)** — refactor su logica delicata e ben testata: meglio
  a comportamento congelato, non durante sviluppo attivo.
- **T1-2 / T1-3 (atomicità/reaper)** — robustezza medio-bassa per single-user; OK
  alla passata pre-UI.
- **T4-1 (dead code engineering/files)** — è codice tuo: non lo rimuovo senza tuo
  via libera esplicito.
