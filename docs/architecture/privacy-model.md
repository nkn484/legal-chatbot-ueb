# Privacy model — design only, not legal advice

## Classification, purpose, and minimization
`PUBLIC` is limited to active published legal source/canonical citation data. `INTERNAL` includes sanitized event/telemetry and Core cryptographic-operation metadata (`DC-16`), never a raw key. `CONFIDENTIAL` includes question, response, artifact, retrieval context, and audit data. `RESTRICTED` includes identity profile, bearer context, originals, LATER backup copies, and separate Provider/source secret references. Collection is purpose-limited and `HUMAN_APPROVAL_REQUIRED`; Feedback/Golden/dataset/evaluation is `FUTURE_SCHEDULE_REQUIRED` and `NOT_COLLECTED_CORE`.

## Retention, deletion, and hold
| Rules | Effective limit / deletion |
|---|---|
| RET-01, RET-02, RET-03 | chat 7d; idempotency 24h; retrieval context/cache 15m |
| RET-04, RET-05, RET-06 | quarantine/rejected 7d; unpublished 30d; published lifecycle-bound and immediate serving removal on revoke/unpublish |
| RET-07, RET-08, RET-09, RET-10 | telemetry 14d; sanitized audit 30d; broker/retry 24h; DLQ 7d |
| RET-11, RET-12, RET-13 | backup/DR `NOT_COLLECTED_CORE`, future approved max 30d; identity lifecycle/delete ≤30d after closure; raw provider tokens never persist and rollback overlap ≤24h |
| RET-14–RET-18 | Provider `NOT_SENT`; Feedback/Golden/dataset/eval `NOT_COLLECTED_CORE`; Core KMS metadata 30d; source secret and endpoint profile are future-only |

Core deletion creates an owner-authorized ledger/tombstone and propagates only to owner stores, projections, caches, events, and DLQ. Backup/DR is separately excluded from Core by `REQ-OPS-002`: `RISK-041`, `CTRL-PRIV-003`, `FLOW-22`/`FLOW-23`, and the `SEC-PRIV-006` deletion-ledger restore test are LATER `DENIED_NOT_SENT`; the restore rule is a future activation gate. Backup encryption and restore evidence are `NOT_MEASURED`. A hold requires named privacy or legal-content authority; policy/legal basis remains undecided and requires human approval. This is not legal advice.

## Encryption and key responsibilities
| Entries | Exact planned protection |
|---|---|
| ENC-01 | identity password verifier: Argon2id one-way |
| ENC-02, ENC-03, ENC-13 | external TLS ≥1.2/prefer 1.3; production mTLS; workload keys ≤30d |
| ENC-04, ENC-05 | Identity and Chat restricted fields: AES-256-GCM envelope, per-service KMS alias |
| ENC-06, ENC-07 | Document object and Processing artifact: separate SSE-KMS/envelope aliases/principals |
| ENC-08 | service DB volume plus field-level restricted data encryption |
| ENC-09 | audit data encryption plus separate checkpoint signing key |
| ENC-10, ENC-11 | broker/telemetry and separately keyed **LATER** backup volumes |
| ENC-12 | Provider HSM/secret manager only, provider principal, ≤90d/on exposure |
| ENC-14, ENC-16 | Identity HSM JWT signing key, ≤90d; separate Document/source secret-manager alias/principal |

All entries are `PLANNED_NOT_IMPLEMENTED`, non-exportable, principal-scoped, with compromise revocation and the recovery procedures in the registry.

## Secret/PII flows and external gates
PII/secret body flows, including gateway routes `FLOW-31`–`FLOW-34`, retrieval/citation validation `FLOW-35`/`FLOW-36`, and separate secret routes `FLOW-37`/`FLOW-38`, use `BODY_FORBIDDEN`. `CTRL-PRIV-001` governs only Core minimization/redaction for chat, upload, telemetry, audit, event, and DLQ paths. `FLOW-24` is Core KMS metadata only (`DC-16`): it cannot carry a Provider/source secret or raw key. Provider flows `FLOW-25`/`FLOW-26`/`FLOW-37` are LATER `DENIED_NOT_SENT` under `CTRL-PRIV-004`; DPA, training, retention, residency, subprocessor, and lawful-basis evidence require human approval before any content egress. Source flows `FLOW-29`/`FLOW-30`/`FLOW-38`, backup/DR `FLOW-22`/`FLOW-23`, and Feedback/Evaluation are also LATER `DENIED_NOT_SENT`.

## Responsibilities
Core authentication is an isolated local/demo boundary only, using secret/config credentials that are never hardcoded, logged, or browser-exposed; it is not production-auth equivalence. Live OIDC/SSO and remote JWKS are LATER and disabled in Core. Each service owns its own data and deletion work; platform-security owns root KMS/HSM while exact DB aliases/principals are listed in `ENC-08`. Audit owns append-only audit data. No raw token, secret, full prompt, or body is permitted in logging.
