# Event delivery semantics — AsyncAPI v1 catalog

The catalog defines a custom JSON envelope v1 over AMQP 0-9-1; it does **not** claim CloudEvents AMQP compliance. It has logical durable topic-exchange/routing-key names only—no broker URL, virtual host, credential, queue, quorum, DLX/TTL topology, or deployment setting.

## Directed command and facts

`legal.document.version.processing.requested.v1` is the only command. It uses `legal.commands`, declares `x-ueb-directed-consumer: processing-service`, and has exactly one document-service sender and one processing-service receiver. The remaining 13 active messages are facts on `legal.events`. Message and operation ACL extensions state the allowed publisher and consumer services.

## Envelope, owner relations, and hashing

Each envelope carries immutable `message_id`, type/version, producer/version, aggregate identity/revision, ordering key, correlation, and `payload_hash`. Owner relation is explicit: for example ProcessingJobSucceeded is `Job(job_id, job_revision)`, ArtifactsReady is `ArtifactSet(artifact_set_id, artifact_set_revision)`, IndexProjectionActivated is `IndexProjection(index_id, projection_revision)`, and DocumentPublished is `Document(document_id, document_revision)`. `ordering_key` equals the owner aggregate ID; `aggregate_revision` is per-owner fencing metadata, not a global sequence/FIFO guarantee.

`payload_hash` is `sha256:` plus SHA-256 of `data` serialized as project canonical JSON: UTF-8, recursively sorted object keys, comma/colon separators without insignificant whitespace, JSON strings/integers/booleans/null only, and arrays preserving order. Floats are forbidden. This is **not RFC JCS**. The offline validator recomputes and verifies this hash for all 30 valid fixtures. Same `message_id` with the same hash is an inbox no-op; the same ID with changed data/hash is an integrity rejection/quarantine.

## Outbox, confirms, inbox, and acknowledgement

The intended local implementation flow is: producer domain effect plus local outbox commits in one local transaction; publisher confirm plus mandatory/unroutable handling establishes broker acceptance; consumer validates authorization/schema/integrity, commits inbox idempotency plus local effect/outbox, then manually acknowledges. Delivery is **at least once**, never exactly once. There is no shared database, distributed transaction, or shared business model. Consumer prefetch is bounded/nonzero and immediate requeue loops are forbidden.

Stale owner revisions are no-ops; a gap reconciles through the owner API. Unpublish/revoke dominates a delayed publish/activation. Processing artifacts must bind the original request's document/version/input hash. Core IndexProjection events use `mode=FTS`; `status` conveys READY, ACTIVE, FAILED, or RETIRED. VECTOR and HYBRID are LATER. `ACTIVE` projection status is operational only and cannot establish legal truth.

Some catalog components carry `x-ueb-planned-consumers` metadata. These seven links are future, non-routable planning metadata: they do not add an active ACL consumer, channel, operation, delivery authorization, or Core side effect.

## Retry, DLQ, and replay

Only transient, idempotent failures retry: five deliveries including the first with jittered 30, 120, 600, and 1800-second delays. Schema, authorization, validation, integrity, and forbidden-state failures go directly to a logical per-consumer/family DLQ. The DLQ stores sanitized failure metadata, never duplicates raw bodies outside the safe envelope, and has no automatic replay. Authorized, rate-limited, audited replay preserves `message_id`; an already completed inbox effect is a no-op.

Main/retry broker retention is a planning maximum of seven days and DLQ retention fourteen days; neither is a legal-retention decision. Prompt 02.6 may shorten them. Audit has a separate 30-day demo maximum. AuditFact is a terminal multi-producer exception; audit-service does not republish an audit event during its own outage.

## References and limits

- [AsyncAPI 3.0.0 specification](https://www.asyncapi.com/docs/reference/specification/v3.0.0)
- [AsyncAPI AMQP 0-9-1 bindings 0.3.0](https://github.com/asyncapi/bindings/tree/master/amqp)
- [RabbitMQ publisher confirms and consumer acknowledgements](https://www.rabbitmq.com/docs/confirms)

These protocol references do not constitute runtime evidence. Broker version/topology, quorum, DLX/TTL configuration, IaC, runtime outbox/inbox/retry, ACL enforcement, and observability remain `NOT_MEASURED`.
