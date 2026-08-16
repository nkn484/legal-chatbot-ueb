# ADR-005: Identity integration provider-neutral

- Status: **ACCEPTED**
- Date: 2026-08-13

## Status history and acceptance lineage

- 2026-08-13: `PROPOSED` in Prompt 02.2 revision 1.
- 2026-08-13T08:10:51.287717+00:00: Status is `ACCEPTED` only because the unchanged substantive content was human-approved for Prompt 02.2 revision 1. Evidence paths recorded in `.agent-run/prompt-state.json`: `docs/architecture/adr/ADR-001-communication.md`, `docs/architecture/adr/ADR-002-persistence-storage-cache.md`, `docs/architecture/adr/ADR-003-monorepo-runtimes.md`, `docs/architecture/adr/ADR-004-observability.md`, `docs/architecture/adr/ADR-005-identity-integration.md`; report: `docs/progress/02.2.md`.
- 2026-08-16: Prompt 02.7 revision 2 reconciles only stale status metadata. Any later substantive change requires a new ADR revision and human approval; this metadata correction does not pre-approve altered ADR content.

## Context

Identity owns identities, roles and service identities; gateway propagates verified context and each domain service authorizes its resource. Core local/demo excludes live SSO; `provider-service` is the LATER answer Provider, not an identity provider. DEC-005 remains OPEN.

## Options considered

1. **Client-declared roles:** nhanh cho demo nhưng caller can forge authority and violates deny-by-default.
2. **Bespoke demo auth only:** small initial surface, but creates a non-portable security model and defers integration boundary.
3. **Full IdP/SSO now:** can be production-like, but adds tenant/MFA/operations scope excluded from ten-day Core.
4. **OAuth2/OIDC-ready provider-neutral boundary:** establishes validation and adapters without claiming a live IdP/SSO deployment.

## Decision

Chọn OAuth2/OIDC-ready provider-neutral boundary, không implement live IdP/SSO. Identity owns identity/role/service identity; gateway verifies và propagates context; từng domain service enforce resource authorization deny-by-default. Anonymous researcher là limited principal rõ ràng. Demo Curator/Admin bootstrap credential chỉ local-demo, lấy từ secret/config mechanism, least privilege, never hardcoded/logged/browser-exposed, không là arbitrary header/frontend guard, bị explicitly rejected/disabled outside demo mode và không ngụ ý production auth.

Khi implement browser/public client dùng Authorization Code + PKCE S256; không implicit hoặc resource-owner-password grant. Cần exact registered redirect matching và TLS. OIDC issuer/discovery/JWKS URL chỉ lấy từ configured allowlist/trusted issuer registry, không từ arbitrary request/client-supplied URL. Parse và normalize URL; chỉ HTTPS; resolve DNS và validate every resolved address, block loopback, RFC1918/private, link-local, multicast/reserved/unspecified ranges và cloud metadata endpoint; chống DNS rebinding bằng connection-time validation khi khả thi. Disable redirects by default, hoặc revalidate every redirect target theo policy này với bounded hop count. Áp strict timeout, response-size/content-type limits, bounded JWKS keys/cache; fail closed khi fetch/parse/refresh error nếu không có valid trusted cached key. Metadata returned issuer phải exactly equal configured expected issuer. Token phải qua signature/alg policy, exact expected issuer và audience/client ID match, expiry/not-before, nonce/state khi applicable; không token nào được trusted nếu chưa qua cả cryptographic validation và configured issuer/audience policy. Tách ID token/access token và user/service identity. Không log hoặc read back token/credential. Exact IdP, tenant, MFA và service auth để sau.

## Consequences

### Positive

- Tạo migration path chuẩn mà không mở rộng Core thành SSO implementation.
- Resource authorization vẫn ở owner service, không trust client role hay gateway-only enforcement.

### Negative/trade-offs

- Cần future integration/test cho key rotation, redirect, issuer và service identity.
- Demo bootstrap và production equivalence không được chứng minh; security integration là NOT_MEASURED.

## Rejected options

- Client-declared roles và arbitrary trusted header bị từ chối vì forged context risk.
- Full IdP/SSO now bị từ chối vì ngoài Core, không phải vì OAuth/OIDC không phù hợp.
- Bespoke-only demo auth bị từ chối vì không tạo provider-neutral integration boundary.

## Constraints and guardrails

No token/credential logging/readback; auth failure và untrusted issuer/JWKS retrieval fail closed. OIDC remote retrieval phải áp allowlist/trusted issuer registry, URL/DNS/address/redirect policy, connection-time DNS-rebinding defense khi khả thi, timeout và response bounds nêu trong Decision. Không cross-service DB/shared business model. Exact endpoint/claim schema/field, IdP, version/image chỉ pin sau compatibility/security/license review và digest/lockfile. Kafka, Kubernetes và HA không là Core MUST. DEC-005 OPEN; ADR không giải quyết manifest hoặc claim executable Citation path.

## Reconsideration triggers

Xem xét live IdP/SSO, MFA, tenant topology hoặc service-auth mechanism khi approved deployment, threat model, credential operations và measured integration requirements tồn tại.

## Related boundaries and rules

Giữ 12 logical contexts và DAG 02.1; identity-service cung cấp verified context, domain service tự authorize, audit-service không authorize. Áp dụng HR-08..14, HR-23..28, HR-36..42.

## References

- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [RFC 9700 OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700)
- [RFC 7636 PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 8414 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414)
