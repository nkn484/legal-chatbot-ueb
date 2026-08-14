# Event ownership matrix — AsyncAPI v1 catalog

This contract catalog has no broker topology. `7/14` means planning maximum main/retry and DLQ days. Every row is fenced by `aggregate_revision`, has `ordering_key == aggregate_id`, and is deduplicated as `(consumer_service,message_id)`.

| Message type | Producer | Active consumers | Planned non-routable consumers | Kind | Producer-owned aggregate relation (ID / revision) | Activation / route | Retention | Retry / DLQ |
|---|---|---|---|---|---|---|---|
| `legal.document.version.processing.requested.v1` | document-service | processing-service | — | COMMAND | Version: `version_id` / `version_revision` | CORE / `legal.commands` directed | 7/14 | transient-idempotent / family |
| `legal.processing.job.succeeded.v1` | processing-service | document-service | — | EVENT | Job: `job_id` / `job_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.processing.job.failed.v1` | processing-service | document-service | — | EVENT | Job: `job_id` / `job_revision` | CORE / `legal.events` | 7/14 | permanent-or-transient / family |
| `legal.processing.artifacts.ready.v1` | processing-service | index-service | — | EVENT | ArtifactSet: `artifact_set_id` / `artifact_set_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.document.published.v1` | document-service | index-service | — | EVENT | Document: `document_id` / `document_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.document.unpublished.v1` | document-service | index-service | — | EVENT | Document: `document_id` / `document_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.document.archived.v1` | document-service | index-service | — | EVENT | Document: `document_id` / `document_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.document.source.invalidated.v1` | document-service | citation-service | feedback-service; evaluation-service | EVENT | Document: `document_id` / `document_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.document.source.revoked.v1` | document-service | citation-service | feedback-service; evaluation-service | EVENT | Document: `document_id` / `document_revision` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.index.projection.ready.v1` | index-service | document-service | — | EVENT | IndexProjection: `index_id` / `projection_revision`; `mode=FTS`, `status=READY` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.index.projection.activated.v1` | index-service | document-service | — | EVENT | IndexProjection: `index_id` / `projection_revision`; `mode=FTS`, `status=ACTIVE` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.index.projection.failed.v1` | index-service | document-service | — | EVENT | IndexProjection: `index_id` / `projection_revision`; `mode=FTS`, `status=FAILED` | CORE / `legal.events` | 7/14 | permanent-or-transient / family |
| `legal.index.projection.retired.v1` | index-service | document-service | — | EVENT | IndexProjection: `index_id` / `projection_revision`; `mode=FTS`, `status=RETIRED` | CORE / `legal.events` | 7/14 | transient-idempotent / family |
| `legal.audit.fact.observed.v1` | allowlisted application services* | audit-service | — | EVENT | AuditObservation: `observation_id` / `observation_revision` | CORE / `legal.events` | 7/14† | transient-idempotent / family |
| Provider configuration (4 LATER types) | provider-service | — | — | EVENT | ProviderConfiguration: `configuration_id` / `configuration_revision` | LATER / no | 7/14 | not implemented |
| Chat answer snapshot | chat-service | — | feedback-service | EVENT | ChatAnswer: `answer_id` / `answer_revision` | LATER / no | 7/14 | not implemented |
| Feedback recorded / annotation requested | feedback-service | — | — | EVENT | Feedback: `feedback_id` / `feedback_revision` | LATER / no | 7/14 | not implemented |
| Golden approved / revoked | feedback-service | — | evaluation-service | EVENT | GoldenAnswer: `golden_answer_id` / `golden_revision` | LATER / no | 7/14 | not implemented |
| Dataset frozen / revoked | evaluation-service | — | — | EVENT | Dataset: `dataset_id` / `dataset_revision` | LATER / no | 7/14 | not implemented |
| Evaluation completed / failed | evaluation-service | — | — | EVENT | Evaluation: `evaluation_id` / `evaluation_revision` | LATER / no | 7/14 | not implemented |
| Candidate evaluated / eligible / withdrawn | evaluation-service | — | — | EVENT | Candidate: `candidate_id` / `candidate_revision` | LATER / no | 7/14 | not implemented |

* AuditFact producers are identity-service, document-service, processing-service, index-service, retrieval-service, citation-service, chat-service, feedback-service, evaluation-service, and provider-service. Audit-service is excluded, terminal, and internally assigns its canonical audit record; `AuditObservation` is producer-owned observation metadata, not that record. †Audit has a separate 30-day demo maximum and it is not inferred from catalog retention.

## Boundary rules

- The only command is a single-target document-service → processing-service message on `legal.commands`; its channel extension and ACL name processing-service as directed consumer. All Core facts use `legal.events`.
- Processing relations bind document/version/input hash while their aggregate is Job or ArtifactSet. Index `mode` is always `FTS` for these Core events; lifecycle is the `status` field. VECTOR and HYBRID modes are LATER. `ACTIVE` is operational projection status only, never legal truth. Document and citation consumers still perform live owner checks.
- Planned consumer metadata is non-routable: it does not expand the active ACL, create a channel/operation, or authorize delivery. It records seven approved future consumer links only.
- Golden approval carries `approval_snapshot_id`, `approval_snapshot_hash`, nonempty citation validation IDs, opaque approver reference, and answer hash—not answer content. Dataset freeze carries manifest, lineage, approved-Golden-set evidence, count, and timestamp.
- LATER entries are components-only planning artifacts: no channel/operation, activation/release/train/deploy/provider-call action, or Core side effect. Candidate eligibility is recommendation only.

## Prohibited events and payloads

No provider endpoint/base URL, secret reference/key, credential, prompt, question, answer, comment, raw document text, excerpt, storage location/key, signed URL, raw payload, full snapshot, current state, or legal-content array may be published. No automatic event may activate a provider/candidate, release/deploy/train a model, or convert feedback into Golden Answer/dataset ground truth.
