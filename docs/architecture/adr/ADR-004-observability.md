# ADR-004: Observability tối thiểu và privacy-by-default

- Status: **ACCEPTED**
- Date: 2026-08-13

## Status history and acceptance lineage

- 2026-08-13: `PROPOSED` in Prompt 02.2 revision 1.
- 2026-08-13T08:10:51.287717+00:00: Status is `ACCEPTED` only because the unchanged substantive content was human-approved for Prompt 02.2 revision 1. Evidence paths recorded in `.agent-run/prompt-state.json`: `docs/architecture/adr/ADR-001-communication.md`, `docs/architecture/adr/ADR-002-persistence-storage-cache.md`, `docs/architecture/adr/ADR-003-monorepo-runtimes.md`, `docs/architecture/adr/ADR-004-observability.md`, `docs/architecture/adr/ADR-005-identity-integration.md`; report: `docs/progress/02.2.md`.
- 2026-08-16: Prompt 02.7 revision 2 reconciles only stale status metadata. Any later substantive change requires a new ADR revision and human approval; this metadata correction does not pre-approve altered ADR content.

## Context

Core cần correlation cho REST, RabbitMQ, DB và job mà không biến telemetry thành kho legal content, PII hoặc secret. Audit là canonical append-only owner riêng; observability không thay đổi 12 context/DAG và DEC-005 OPEN.

## Options considered

1. **Logs only:** ít thành phần nhưng khó nối request/job/service và khó aggregate SLO-like signal.
2. **Vendor APM:** trải nghiệm tích hợp tốt, nhưng tăng lock-in/cost/data-export concern trước Core evidence.
3. **OpenTelemetry + Prometheus:** chuẩn mở cho trace context/structured correlation và scrape metrics, có thể thêm Collector sau.
4. **Full content capture:** debug thuận tiện ngắn hạn nhưng rủi ro disclosure của prompt/document/auth data không chấp nhận được.

## Decision

Dùng OpenTelemetry API/SDK/context cho traces và structured correlation, Prometheus scrape metrics. Collector có thể dùng sau nhưng không mandatory Core/HA. Instrument HTTP, RabbitMQ producer/consumer, DB và jobs; quan hệ causal async dùng propagation hoặc links khi phù hợp.

Telemetry allowlist: service.name/version, environment, route template, operation, status/error class, duration, bounded queue/job state/counts, trace/correlation IDs trong logs/traces. Không dùng unbounded ID làm metric label. Default deny bodies, prompts, questions, retrieved context, document text/excerpts, event payloads, authorization headers, cookies, tokens, secrets, PII, raw SQL/query values và raw exception payloads. Redact trước export/storage; metric labels low-cardinality. Audit-service giữ canonical append-only ownership và là retention owner. 14-day redacted technical-log cap và 30-day admin-audit cap là user-approved Core-demo planning maxima inherited from scope; chúng không là general legal/business retention policy hoặc implemented enforcement. Prompt 02.6 privacy model phải validate hoặc shorten các maxima này và assign deletion/legal-hold rules trước implementation; nếu law/policy đòi duration khác, privacy decision được phê duyệt sẽ supersede. Product enforcement là NOT_MEASURED.

## Consequences

### Positive

- Trace/correlation hỗ trợ debug bounded xuyên REST, broker, DB và job mà không chuyển business ownership.
- Allowlist/redaction giảm rủi ro HR-23 và HR-38.

### Negative/trade-offs

- Instrumentation, context propagation và cardinality discipline cần effort/test.
- Product telemetry tests, exporter behavior và retention enforcement là NOT_MEASURED.

## Rejected options

- Logs only không đủ causal visibility cho async work.
- Vendor APM không là Core decision vì lock-in/cost/privacy review chưa có.
- Full content capture bị từ chối vì disclosure risk.

## Constraints and guardrails

Không log/read back secret, token hoặc full context. OTel/Prometheus versions pin sau compatibility/security/license checks, digest/lockfile. Kafka, Kubernetes và HA không là Core MUST. Không cross-service DB/shared business model. DEC-005 OPEN, không đổi manifest hay claim executable Citation path.

## Reconsideration triggers

Xem xét Collector, exporter hoặc retention policy khi Prompt 02.6 privacy model, measured volume/cost, incident needs hoặc compliance requirements được phê duyệt.

## Related boundaries and rules

Giữ 12 logical contexts và 02.1 DAG; audit-service vẫn owner audit canonical và service khác chỉ gửi audit facts async. Áp dụng HR-12, HR-22, HR-23, HR-35, HR-36..40.

## References

- [OpenTelemetry specification](https://opentelemetry.io/docs/specs/otel/)
- [OpenTelemetry resources](https://opentelemetry.io/docs/specs/semconv/resource/)
- [OpenTelemetry trace API](https://opentelemetry.io/docs/specs/otel/trace/api/)
- [OpenTelemetry Prometheus exporter](https://opentelemetry.io/docs/languages/python/exporter/)
- [Prometheus overview](https://prometheus.io/docs/introduction/overview/)
- [OpenTelemetry license](https://github.com/open-telemetry/opentelemetry-specification/blob/main/LICENSE)
- [Prometheus license](https://github.com/prometheus/prometheus/blob/main/LICENSE)
