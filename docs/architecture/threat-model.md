# Threat model — Prompt 02.6 design candidate

## Scope and design warning
This is a design-only security model for the 12 bounded services, their owners, and planned Core/LATER capabilities. It is **not** an implementation claim: all runtime controls and tests are `NOT_MEASURED`; every risk is `OPEN_PLANNED`, `NOT_ACCEPTED`, and Critical/High capability activation is blocked until its tests run. `DEC-005` remains **OPEN**.

## Methodology, assets, actors, and boundaries
STRIDE is assessed per `TB-01` through `TB-13`, using likelihood × impact (Critical 20–25, High 12–19). Assets include identity context, originals, artifacts, PUBLISHED legal versions, retrieval lineage, canonical citations, audit evidence, keys, and backups. Actors are public users, administrators, malicious insiders, compromised workloads, upstream attackers, and future providers/connectors. The authoritative boundary list is `contracts/security/privacy-data-map.yaml`.

## STRIDE and OWASP mappings
All STRIDE categories are covered: Spoofing (identity, broker), Tampering (documents/events/citations), Repudiation (audit), Information disclosure (PII/cache/object), Denial of service (parser/resource), and Elevation of privilege (BOLA/service identity). OWASP LLM Top 10 2025 `LLM01`–`LLM10` and the full OWASP API Security Top 10 2023 `API1, API2, API3, API4, API5, API6, API7, API8, API9, API10` are mapped per risk. References: <https://owasp.org/www-project-top-10-for-large-language-model-applications/> and <https://owasp.org/API-Security/>.

## Risk register and activation gate
| ID | Title | Severity | Owner | Tests | Activation gate |
|---|---|---|---|---|---|
| RISK-001 | Forged admin publish | Critical | document-service | SEC-AUTH-001/002/005 | BLOCKED_UNTIL_VERIFIED |
| RISK-002 | Authorization bypass | High | document-service | SEC-AUTH-004/005/007 | BLOCKED_UNTIL_VERIFIED |
| RISK-003 | Review hash change | High | document-service | SEC-AUTH-002/003, SEC-PDF-006 | BLOCKED_UNTIL_VERIFIED |
| RISK-004 | Session replay | High | identity-service | SEC-AUTH-006/007 | BLOCKED_UNTIL_VERIFIED |
| RISK-005 | JWT confusion | Critical | identity-service | SEC-AUTH-008/010 | BLOCKED_UNTIL_VERIFIED |
| RISK-006 | JWKS SSRF | High | identity-service | SEC-AUTH-009 | BLOCKED_UNTIL_VERIFIED |
| RISK-007 | Forged context | High | identity-service | SEC-AUTH-007/008 | BLOCKED_UNTIL_VERIFIED |
| RISK-008 | Lateral identity | High | platform-security | SEC-AUTH-010/EVT-001/DB-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-009 | PDF bomb | High | processing-service | SEC-PDF-004/RES-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-010 | Parser exploit | High | processing-service | SEC-PDF-005/SC-002 | BLOCKED_UNTIL_VERIFIED |
| RISK-011 | Malware upload | High | document-service | SEC-PDF-001/002 | BLOCKED_UNTIL_VERIFIED |
| RISK-012 | Object leak | High | document-service | SEC-PDF-003/DB-002 | BLOCKED_UNTIL_VERIFIED |
| RISK-013 | Immutable overwrite | High | document-service | SEC-PDF-006/DB-002 | BLOCKED_UNTIL_VERIFIED |
| RISK-014 | Corpus injection | High | processing-service | SEC-RAG-001/CITE-004 | BLOCKED_UNTIL_VERIFIED |
| RISK-015 | Forged quality | High | processing-service | SEC-RAG-002/AUD-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-016 | Revoked retrieval | Critical | retrieval-service | SEC-RAG-003/004/005 | BLOCKED_UNTIL_VERIFIED |
| RISK-017 | Forged lineage | High | retrieval-service | SEC-RAG-006/007 | BLOCKED_UNTIL_VERIFIED |
| RISK-018 | Citation spoof | Critical | citation-service | SEC-CITE-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-019 | Insufficiency override | Critical | chat-service | SEC-CITE-004/002 | BLOCKED_UNTIL_VERIFIED |
| RISK-020 | Unsafe output | High | chat-service | SEC-OUT-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-021 | Provider SSRF | Critical | provider-service | SEC-SSRF-001..005 | BLOCKED_UNTIL_VERIFIED |
| RISK-022 | Provider secret leak | Critical | provider-service | SEC-SSRF-006/PRIV-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-023 | Provider race | High | provider-service | SEC-SSRF-007/REL-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-024 | Provider agency | High | provider-service | SEC-SSRF-005/PRIV-003/REL-002 | BLOCKED_UNTIL_VERIFIED |
| RISK-025 | Core PII/secret path | Critical | privacy-owner | SEC-PRIV-001/002/005 | BLOCKED_UNTIL_VERIFIED |
| RISK-026 | Prompt leakage | High | chat-service | SEC-PRIV-004/OUT-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-027 | Feedback poisoning | High | feedback-service | SEC-REL-001/PRIV-003 | BLOCKED_UNTIL_VERIFIED |
| RISK-028 | Golden approval | High | feedback-service | SEC-AUTH-007/CITE-002 | BLOCKED_UNTIL_VERIFIED |
| RISK-029 | Dataset leakage | High | evaluation-service | SEC-PRIV-005/REL-002 | BLOCKED_UNTIL_VERIFIED |
| RISK-030 | Vector disclosure | High | index-service | SEC-CACHE-001/PRIV-001 | BLOCKED_UNTIL_VERIFIED |
| RISK-031 | Auto-release | Critical | release-owner | SEC-REL-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-032 | Event spoofing | High | platform-security | SEC-EVT-001/004 | BLOCKED_UNTIL_VERIFIED |
| RISK-033 | Event reorder | High | platform-security | SEC-EVT-002/003/004 | BLOCKED_UNTIL_VERIFIED |
| RISK-034 | Poison DLQ | High | platform-security | SEC-EVT-005/006 | BLOCKED_UNTIL_VERIFIED |
| RISK-035 | Cross-service DB/object-prefix | High | platform-security | SEC-DB-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-036 | Audit tamper | High | audit-service | SEC-AUD-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-037 | Supply chain | Critical | platform-security | SEC-SC-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-038 | Unbounded consumption | High | api-gateway | SEC-RES-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-039 | Cache disclosure | High | chat-service | SEC-CACHE-001/002 | BLOCKED_UNTIL_VERIFIED |
| RISK-040 | Source connector | High | document-service | SEC-SOURCE-001/002/003 | BLOCKED_UNTIL_VERIFIED |
| RISK-041 | Future backup disclosure/restore | High | platform-security | SEC-PRIV-006 | BLOCKED_UNTIL_VERIFIED |

## Top attack chains and controls
Stolen admin context → publish is stopped by MFA, duty separation, immutable hash and audit controls. Hostile PDF → parser is constrained by quarantine, MIME/AV gate, no-egress sandbox and budgets. Stale index → answer is stopped by final owner eligibility and Citation recheck; Retrieval returns evidence/sufficiency to Chat, and Chat alone transfers the opaque request-bound context to Citation. Event impersonation is stopped by broker-authenticated mTLS connection identity and ACL, schema/type/revision/payload-hash validation (hash is integrity, not authentication). Future Provider/source egress is default denied.

## Core/LATER reconciliations
Core identity is an isolated `local/demo` credential boundary with signed downstream context and workload mTLS; it is not production-auth equivalence. Live OIDC/SSO and remote JWKS are LATER (`RISK-005`, `RISK-006`, `SEC-AUTH-008`, `SEC-AUTH-009`) and remain disabled. Core privacy `RISK-025` covers only chat/upload/identity/log/trace/audit/event/DLQ paths and Core tombstone propagation through `CTRL-PRIV-001`/`CTRL-PRIV-002`. Provider content egress `RISK-024` is LATER-only under `CTRL-PRIV-004` and its DPA/training/retention/residency/subprocessor/lawful-basis gate. Backup/DR is excluded from Core by `REQ-OPS-002`: `RISK-041`, `CTRL-PRIV-003`, its flows, and `SEC-PRIV-006` restore/deletion-ledger test are LATER, and backup encryption/restore evidence is `NOT_MEASURED`. Core immutability (`RISK-013`) and data-plane isolation (`RISK-035`) cover only object/version and database/object-prefix protections. All LATER flows, including backup/DR, Provider, Feedback/Evaluation, and source connector families, remain `DENIED_NOT_SENT` until separate approval and measured evidence.

## Risk acceptance
There is no accepted risk. Raw-secret disclosure, citation/publish bypass, SSRF, auto-release, cross-service data-plane access, and unmeasured Critical/High risks are never acceptable. A named non-production demo exception may be proposed for at most 30 days but cannot waive a blocker; prompt approval is not risk acceptance.
