# 079 — AUTONOMOUS-DEVELOPMENT-LOOP-0: minimal scheduled continuation

Status: full specification, ready for implementation after the dated readiness decision in `079-readiness-2026-08-01.md` is merged and `docs/specs/STATUS.md` records `ready`.

Depends on: 022

## 1. Acceptance criterion

When one already-authorized implementation session is interrupted, JarvisOS repository work resumes without a new maintainer message, on the same pull request branch, for the same spec, and against the same exact head.

V0 satisfies this criterion with one GitHub Actions workflow scheduled once per day. The workflow reconstructs all authority from state that already exists in GitHub:

- the single `in_review` row and implementation PR number in `docs/specs/STATUS.md`;
- the open pull request, its base, head repository, head branch and exact head SHA;
- the branch and commit history;
- deterministic workflow runs and one idempotency marker in the PR conversation.

No additional authority file, control branch, database, queue, lease, claim registry, GitHub App, organization, repository or credential is required.

## 2. Test del minimo necessario

### Test del minimo necessario
Criterio di accettazione della spec:
Una sessione interrotta riprende da sola, sullo stesso ramo e sulla stessa spec, senza un nuovo messaggio del maintainer.

Questo lavoro serve a soddisfarlo?           sì

Il criterio è raggiungibile senza di esso?   no — senza un trigger futuro non esiste alcun processo che osservi il fronte interrotto e pubblichi la richiesta di continuazione.

Il criterio è raggiungibile con meno infrastruttura? sì — un singolo workflow schedulato, il `GITHUB_TOKEN` già fornito da Actions e lo stato GitHub esistente sono sufficienti.

Conseguenza vincolante: non costruire App, webhook, servizio, database, coda, control branch, lease, compare-and-swap remoto, ruleset di prova o repository sandbox per 079 v0. Il precedente proof CAS resta evidenza allegata di una possibile estensione, non una dipendenza.

## 3. Scope

079 comprende esclusivamente:

1. individuare deterministicamente l'unica spec di implementazione `in_review`;
2. verificare che il numero PR registrato esista e identifichi una PR aperta nello stesso repository;
3. verificare base `master`, ramo head non protetto e exact head SHA;
4. rifiutare ambiguità, più fronti attivi, PR chiusa, fork, branch mancante o stato incoerente;
5. pubblicare al massimo una richiesta di continuazione per la tupla `(spec, PR, exact head)`;
6. non fare nulla quando la stessa tupla è già stata richiesta;
7. poter essere eseguito manualmente in modalità `dry_run` per prova e diagnosi;
8. registrare l'esito nel log del workflow.

La richiesta di continuazione deve dire all'attuatore già installato di lavorare sulla stessa PR e sullo stesso ramo, rispettare la spec e `AGENTS.md`, non cambiare scope, non modificare segreti o workflow e non eseguire merge.

## 4. Separazione da review/fix

La separazione implementatore/revisore, la classificazione dei rilievi, la correzione e la ri-revisione non appartengono a 079.

Quella capacità è definita separatamente da spec 080 `AUTONOMOUS-REVIEW-REPAIR-0`. 080 può essere rimossa senza rimuovere la continuazione giornaliera di 079. Il workflow 079:

- non legge né risolve thread di review;
- non decide se un rilievo è vero o falso;
- non chiede review;
- non chiede fix di review;
- non esegue merge;
- non modifica label o stato della spec.

## 5. Workflow

Path previsto: `.github/workflows/daily-development-continuation.yml`.

Trigger:

```yaml
on:
  schedule:
    - cron: "17 4 * * *"
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        default: true
```

Il workflow usa:

```yaml
concurrency:
  group: jarvis-development-continuation
  cancel-in-progress: false
```

Permessi massimi:

```yaml
permissions:
  contents: read
  pull-requests: read
  issues: write
```

Non sono ammessi `contents: write`, `actions: write`, secret aggiuntivi, token personali o checkout di un ramo modificabile.

## 6. Deterministic discovery

Lo script previsto è `scripts/daily_development_continuation.py`.

Parsing del registry:

- accetta solo righe tabellari valide;
- considera attive solo `in_progress` e `in_review`;
- v0 continua soltanto `in_review`, perché una PR esistente è il minimo contesto durevole che lega spec e ramo;
- richiede esattamente una riga `in_review` e nessuna diversa riga attiva;
- estrae un solo numero PR dalla colonna `Implementation PR`;
- ogni ambiguità termina con zero commenti e exit non-zero.

Verifica PR:

- repository head uguale al repository base;
- base ref `master`;
- head ref diverso da `master` e `main`;
- PR `open`, non draft;
- exact head presente e di 40 caratteri esadecimali;
- spec a tre cifre presente nel titolo, nel ramo o nel corpo della PR;
- il numero della spec deve coincidere con la riga registry.

## 7. Idempotency

La chiave è:

`sha256(repository + spec + pr_number + exact_head + schema_version)`

Il commento contiene:

```text
<!-- jarvis-continuation:v1:<digest> -->
```

Prima di pubblicare, lo script legge tutti i commenti della PR e cerca esattamente il marker. Se esiste, ritorna successo senza una seconda richiesta.

Il testo operativo contiene l'exact head. Un nuovo commit produce una nuova chiave ed è quindi eleggibile al ciclo giornaliero successivo. Nessuna chiave è conservata altrove.

## 8. Fail-closed conditions

Zero commenti e fallimento deterministico per:

- nessun fronte o più fronti attivi;
- stato `in_progress` senza PR;
- più righe `in_review`;
- PR assente, chiusa, draft o fork;
- base diversa da `master`;
- head protetto o SHA invalido;
- spec non riconciliabile con PR/ramo;
- errore API, risposta incompleta o paginazione non conclusa;
- marker con stessa chiave e testo incompatibile;
- permessi insufficienti.

Uno stato semplicemente non eleggibile usa exit code 0 con `action=noop`; un'incoerenza di autorità usa exit code non-zero.

## 9. Tests

Tutti i test sono offline con HTTP fake.

Obbligatori:

1. parsing di una singola riga `in_review`;
2. rifiuto di zero o più fronti;
3. rifiuto di `in_progress` senza PR;
4. rifiuto di PR chiusa, draft, fork o base errata;
5. rifiuto di spec mismatch;
6. marker deterministico;
7. primo run pubblica una richiesta;
8. replay sullo stesso head non pubblica;
9. nuovo head produce una nuova richiesta;
10. `dry_run` non pubblica;
11. errore/paginazione API non produce side effect;
12. self-test del workflow senza rete o provider.

Nessun test può menzionare realmente `@codex`, effettuare chiamate a provider o consumare quota. Il client fake deve registrare il payload che sarebbe inviato.

## 10. Acceptance proof

La prova di accettazione ha due livelli:

1. **Deterministico offline:** i test dimostrano discovery, exact-head binding, idempotenza e zero side effect sui casi non eleggibili.
2. **GitHub Actions reale senza provider:** dopo il merge, un `workflow_dispatch` in `dry_run=true` deve identificare correttamente una PR campione o produrre `noop` quando non esiste un fronte. La schedulazione giornaliera e il gruppo di concorrenza sono verificati dalla definizione workflow e dal run GitHub.

L'invio reale della richiesta di continuazione non è un test CI e non viene forzato per creare lavoro artificiale. Avverrà sul primo fronte reale eleggibile con `dry_run=false`.

## 11. Non-goals

- review, fix o ri-review automatici;
- merge o auto-merge;
- selezione autonoma di una nuova spec;
- continuazione prima dell'apertura di una PR;
- più fronti o più repository;
- daemon, webhook o polling più frequente di una volta al giorno;
- nuovi account, credenziali o archivi di stato;
- provider routing, budget ledger o contabilità;
- App, ruleset, branch protection o capability wrapper;
- recupero da force-push o ref race;
- modifica di JarvisOS runtime, Hermes, backend o frontend.

## 12. Rollback

La capacità è rimossa eliminando un workflow e uno script. Nessuno stato applicativo o schema deve essere migrato. I marker PR restano cronologia innocua.

## 13. Definition of done

- workflow e script implementati;
- test offline verdi;
- full repository CI verde;
- workflow permissions conformi;
- dry-run GitHub Actions osservato;
- nessun nuovo secret, account, repository o stato durevole;
- `STATUS.md` registra 079 `merged` dopo integrazione;
- 080 resta una spec separata e non implementata.
