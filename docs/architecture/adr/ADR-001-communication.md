# ADR-001: Giao tiếp đồng bộ và bất đồng bộ

- Status: **ACCEPTED**
- Date: 2026-08-13

## Status history and acceptance lineage

- 2026-08-13: `PROPOSED` in Prompt 02.2 revision 1.
- 2026-08-13T08:10:51.287717+00:00: Status is `ACCEPTED` only because the unchanged substantive content was human-approved for Prompt 02.2 revision 1. Evidence paths recorded in `.agent-run/prompt-state.json`: `docs/architecture/adr/ADR-001-communication.md`, `docs/architecture/adr/ADR-002-persistence-storage-cache.md`, `docs/architecture/adr/ADR-003-monorepo-runtimes.md`, `docs/architecture/adr/ADR-004-observability.md`, `docs/architecture/adr/ADR-005-identity-integration.md`; report: `docs/progress/02.2.md`.
- 2026-08-16: Prompt 02.7 revision 2 reconciles only stale status metadata. Any later substantive change requires a new ADR revision and human approval; this metadata correction does not pre-approve altered ADR content.

## Context

Mười hai logical context và synchronous DAG của 02.1 được giữ nguyên. Core có mười ngày lịch, local/demo, FTS tối thiểu và không có answer Provider; Provider, Feedback và Evaluation là LATER. Cần truyền lệnh/query có giới hạn và xử lý extraction, indexing, audit, invalidation không chờ lâu mà không tạo shared database hay executable Citation path khi DEC-005 vẫn OPEN.

## Options considered

1. **All REST:** dễ bắt đầu và phù hợp query/command ngắn, nhưng làm caller chờ tác vụ dài và khó tách retry, replay, consumer độc lập.
2. **Broker-only:** tách thời gian tốt, nhưng không tự nhiên cho request/response có deadline và làm các capability truy vấn đơn giản phức tạp hơn.
3. **REST + RabbitMQ:** REST giữ tương tác giới hạn; broker chuyển durable work và domain fact giữa owner/consumer độc lập.
4. **Kafka/event streaming:** retention và fan-out/replay mạnh hơn, đổi lại tăng vận hành và chưa có nhu cầu throughput/retention được đo ở Core.

## Decision

Dùng REST chỉ cho bounded query/command tức thời, với deadline/time budget và không retry vô hạn. Dùng RabbitMQ cho long-running jobs và domain facts của Document, Processing, Index, audit, invalidation và workflow LATER. Gateway chỉ route/propagate verified context, không business aggregation; không có long synchronous wait.

RabbitMQ là at-least-once, không tuyên bố exactly-once. Mỗi service publisher dùng transactional outbox cục bộ; publisher confirm và xử lý unroutable publish. Consumer dùng inbox/idempotency, manual acknowledgement chỉ sau local commit, retry hữu hạn với backoff+jitter, DLQ quan sát được và quy trình replay. Event có correlation ID, aggregate ID và revision; consumer từ chối stale event hoặc reconcile. Event không là shared DB; không đưa secret hay full document text trừ khi contract sau này chứng minh bắt buộc.

## Consequences

### Positive

- Thực thi HR-11/HR-12 cho durable work, cho phép consumer độc lập và truy vết causal.
- REST vẫn rõ ràng cho capability trong DAG và không ép tất cả luồng thành messaging.

### Negative/trade-offs

- Outbox/inbox, reconciliation, DLQ/replay và correlation làm tăng vận hành và test.
- At-least-once có thể giao trùng và cần idempotency; không có bảo đảm exactly-once.

## Rejected options

- All REST không đáp ứng tốt tác vụ dài và retry durable trong Core.
- Broker-only không phù hợp bounded synchronous query/command.
- Kafka/event streaming bị từ chối như Core MUST, không phải vì không hợp lệ mà vì chưa có evidence cho retention, replay, throughput hoặc many-consumer.

## Constraints and guardrails

Không cross-service SQL/ORM/DB hay shared business model. Schema, field, endpoint, event name/protocol chính xác là concern contract sau này. Retry chỉ lỗi transient/idempotent; payload có giới hạn và không log nội dung nhạy cảm. Kafka, Kubernetes và HA không là Core MUST. Exact versions/images chỉ pin sau compatibility, security, license review, immutable digest/lockfile. DEC-005 OPEN, ADR này không đổi manifest hay claim executable Citation path.

## Reconsideration triggers

Xem xét Kafka sau phê duyệt khi có nhu cầu retention/replay, throughput hoặc many-consumer được đo. Xem xét transport khác khi deadline, failure hoặc operation evidence cho thấy RabbitMQ/REST không đáp ứng.

## Related boundaries and rules

Tuân thủ container-map 02.1: Document/Processing/Index/audit/invalidation event family và DAG không đổi; owner dữ liệu không đổi. Áp dụng HR-08..14, HR-22, HR-36..39; bảo vệ HR-15..18 và HR-23.

## References

- [RabbitMQ publisher confirms](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ publishers](https://www.rabbitmq.com/docs/publishers)
- [RabbitMQ dead letter exchanges](https://www.rabbitmq.com/docs/dlx)
- [RabbitMQ releases](https://www.rabbitmq.com/release-information)
- [RabbitMQ Erlang compatibility](https://www.rabbitmq.com/docs/which-erlang)
- [Microsoft event-driven architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven)
