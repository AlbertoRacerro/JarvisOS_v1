# 059b configuration and pricing ownership

Status: binding companion to `059b-ip-egress-enforcement.md` and
`059b-implementation-clarifications.md`.

## Global policy

The exact policy path is `configs/ai_egress_policy.json`. One strict loader owns
schema/version validation and the canonical policy digest. Alternate policy files or
scattered fallback constants are not permitted.

## Concrete pricing

Execution pricing extends the existing provider/model registry in
`configs/ai_providers.yaml`; 059b must not create a second provider registry.

Every selected network-capable model requires validated metadata for:

- USD input price per one million tokens;
- USD output price per one million tokens;
- pricing version;
- pricing effective timestamp.

The provider-registry loader exposes this concrete price record to 059b. Missing or
invalid pricing for a selected network binding fails closed. Local, fake, or disabled
models may omit paid pricing.

The current route-level cost estimates may remain for user-facing proposal previews,
but they are advisory only and cannot authorize execution or override the concrete
provider/model price. Each fallback resolves its own price record.

## Required checks

- loading policy from any other path fails;
- malformed policy or pricing fails closed;
- a network-capable model without concrete pricing makes zero adapter calls;
- provider/model pricing changes alter the decision and packet binding;
- route-preview pricing cannot authorize a differently priced fallback.

This file changes definition only. It does not add configuration, pricing, provider,
runtime, or external-call behavior.