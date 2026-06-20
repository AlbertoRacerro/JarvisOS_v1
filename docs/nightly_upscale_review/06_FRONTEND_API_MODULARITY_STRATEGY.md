# Frontend And API Modularity Strategy

## Current State

Observed frontend pressure:

- `frontend/src/api/client.ts` combines system, domain, AI, secrets, smoke tests, and smoke console APIs.
- `frontend/src/pages/AIDraft.tsx` combines cost guard, key entry, AI settings, synthetic smoke tests, AI Smoke Console, token meter, and modeling draft.
- `frontend/src/pages/DomainFoundation.tsx` is still temporary and thin, but it will not support a real Workbench without a split.

The UI is still acceptable for local verification. It should not receive the next AI or Workbench feature in its current shape.

## Proposer, Critic, Synthesizer

### Proposal v1

Keep frontend files together until the product UI is redesigned.

### Critique v1

The next additions are not cosmetic. Provider-neutral status/settings, Supervisor AI, artifact browser, runner UI, and Workbench panels all need clearer API and component boundaries. Waiting for a redesign will make the redesign harder.

### Improved Proposal v2

Perform a non-visual modularization before the next major frontend feature:

- split API client by domain;
- split AI page into panels;
- keep CSS and layout visually unchanged;
- keep routes/page names unchanged.

### Critique v2

This is refactor work without user-visible product benefit.

### Final Synthesis

Do a small modular split when provider-neutral AI status/settings are implemented. Avoid redesign. The benefit is lower risk when adding Supervisor or Workbench later.

Residual risk: TypeScript types remain manually synchronized with backend Pydantic models.

## Recommended API Client Split

Target:

```text
frontend/src/api/http.ts
frontend/src/api/system.ts
frontend/src/api/domain.ts
frontend/src/api/ai.ts
frontend/src/api/secrets.ts
frontend/src/api/runner.ts
frontend/src/api/artifacts.ts
```

Rules:

- `http.ts` owns base URL, JSON helpers, error parsing.
- Domain clients own domain types.
- AI client owns AI settings/status/smoke/console/draft types.
- Secrets client owns key status and key entry only.
- Runner client owns job/implementation/run/log/artifact types.
- Artifact client should wait until artifact viewer exists.

## Recommended AI Page Split

Target:

```text
frontend/src/pages/ai/AIDraft.tsx
frontend/src/pages/ai/AICostGuardPanel.tsx
frontend/src/pages/ai/ScalewayKeyPanel.tsx
frontend/src/pages/ai/AISettingsPanel.tsx
frontend/src/pages/ai/SmokeTestsPanel.tsx
frontend/src/pages/ai/SmokeConsolePanel.tsx
frontend/src/pages/ai/DraftRequestPanel.tsx
frontend/src/pages/ai/TokenMeter.tsx
```

Keep the same UI behavior. This is modularity, not redesign.

## Future Supervisor AI Panel

Do not add Supervisor UI until:

- provider-neutral authority decisions exist;
- task types have policy rules;
- audit events are typed;
- provider status/settings are no longer Scaleway-only.

Future Supervisor panel should show:

- task;
- sensitivity status;
- allowed/blocked reason;
- output;
- audit metadata;
- provider/model after completion.

It should not show provider-specific bot buttons.

## Future Provider Diagnostics

Provider diagnostics can show:

- provider id;
- credential status;
- locality;
- enabled/disabled;
- supported capabilities;
- health status;
- last smoke result;
- token/cost status.

Normal workflow panels should not require provider selection.

## Future Artifact Viewer

Artifact viewer should wait for storage strategy implementation. It should consume metadata APIs, not raw filesystem paths.

Panels:

- artifact list;
- type filter;
- run/source linkage;
- metadata details;
- safe preview if supported;
- open/download action through backend endpoint.

## Future Runner UI

Runner UI should wait for V1 runner manifest design.

Panels:

- implementation list;
- manifest detail;
- input form generated from schema;
- job status;
- logs;
- artifacts;
- run detail.

Do not let UI upload arbitrary scripts.

## Future Modeling Workbench

Workbench should be modular from the first commit:

- model spec panel;
- assumptions panel;
- parameters panel;
- equations panel;
- run history panel;
- artifact panel;
- decisions panel;
- AI review panel.

Do not build Workbench inside `DomainFoundation.tsx`.

## API Error Handling

Current frontend throws `Request failed with <status>`. Before richer UI:

- parse `{detail: {code, message}}`;
- preserve safe human message;
- preserve machine code for UI branching;
- handle blocked AI responses as data, not HTTP failures.

## Build And Test Strategy

Do not introduce a heavy frontend test stack yet. For modularization:

- run `npm.cmd run build`;
- add lightweight unit tests only if a test stack already exists;
- otherwise rely on build and manual UI smoke.

