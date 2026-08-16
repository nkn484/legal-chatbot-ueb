# ADR-003: Monorepo và runtime độc lập

- Status: **ACCEPTED**
- Date: 2026-08-13

## Status history and acceptance lineage

- 2026-08-13: `PROPOSED` in Prompt 02.2 revision 1.
- 2026-08-13T08:10:51.287717+00:00: Status is `ACCEPTED` only because the unchanged substantive content was human-approved for Prompt 02.2 revision 1. Evidence paths recorded in `.agent-run/prompt-state.json`: `docs/architecture/adr/ADR-001-communication.md`, `docs/architecture/adr/ADR-002-persistence-storage-cache.md`, `docs/architecture/adr/ADR-003-monorepo-runtimes.md`, `docs/architecture/adr/ADR-004-observability.md`, `docs/architecture/adr/ADR-005-identity-integration.md`; report: `docs/progress/02.2.md`.
- 2026-08-16: Prompt 02.7 revision 2 reconciles only stale status metadata. Any later substantive change requires a new ADR revision and human approval; this metadata correction does not pre-approve altered ADR content.

## Context

Core mười ngày cần delivery đơn giản nhưng phải giữ 12 context và ownership/DAG 02.1. Provider, Feedback và Evaluation chưa khởi động trong Core; local/demo không yêu cầu twelve always-on deployables, Kubernetes hay HA. Client chỉ dùng API được phê duyệt.

## Options considered

1. **Polyrepo:** release/access isolation mạnh, nhưng tăng bootstrap và contract coordination trong thời hạn ngắn.
2. **Monorepo coupled release:** discovery nhanh nhưng buộc deploy chung, làm mất independent evolution.
3. **Monorepo independent deploy:** shared workspace thuận tiện nhưng service giữ artifact/configuration/lifecycle riêng.
4. **Modular monolith/in-process cohost:** ít overhead runtime, nhưng direct model/repository import dễ phá private data boundary.

## Decision

Chọn monorepo với service independently buildable, testable, configurable, migratable, health-checkable và independently deployable. Chỉ generated contracts, telemetry và stable test utilities được share; không share ORM, domain model hay migration. Compose/host local có thể chạy subset, nhưng service vẫn là process/container riêng; không in-process direct repository/model import hay direct database access. Provider/Feedback/Evaluation không bắt đầu trong Core.

Backend Python dùng FastAPI và async I/O khi library awaitable. Blocking I/O dùng thread/process offload có controlled limits; CPU extraction/chunking và durable long task là RabbitMQ worker, không phải request event loop hoặc BackgroundTasks durability. Cần deadline, cancellation, payload limit và graceful shutdown; performance là NOT_MEASURED đến khi test.

Web-chat/admin dùng Next.js và chỉ consume approved public/admin APIs. Generated client từ contract được phê duyệt được phép; cấm backend internal/shared business package/direct service DB/private internal call/browser secret. UI render citation/refusal của backend, không author canonical metadata. Demo auth adapter replaceable; không trust arbitrary header. Exact Node/Python/FastAPI/Pydantic/Next/React versions pin sau supported combinations, digest/lockfile/security scan.

## Consequences

### Positive

- Giữ deploy/data boundary nhưng giảm friction discovery, test utility và generated contract trong demo.
- FastAPI async và worker split tránh chặn request loop cho durable/CPU work.

### Negative/trade-offs

- Repo vẫn cần CI boundary checks, independent configs/migrations và operational discipline.
- Runtime performance/compatibility không được suy đoán; hiện NOT_MEASURED.

## Rejected options

- Coupled-release monorepo và modular monolith bị từ chối vì dễ làm mờ deploy/data boundary.
- Polyrepo không bị đánh giá là sai, nhưng chưa hợp thời hạn Core do coordination cost.

## Constraints and guardrails

Không cross-service DB hoặc shared business model; exact endpoint/event schemas/fields là contract concern sau. Kafka, Kubernetes và HA không là Core MUST. Exact version/image chỉ sau compatibility/security/license checks và immutable image digest/lockfile. DEC-005 OPEN và ADR không đổi manifest hoặc claim executable Citation path.

## Reconsideration triggers

Xem xét repository split hoặc runtime khác chỉ khi team, release, access hoặc performance evidence được đo và phê duyệt.

## Related boundaries and rules

Giữ 12 logical contexts, synchronous DAG, ownership và LATER status của 02.1. Áp dụng HR-08..14, HR-22, HR-23, HR-27, HR-36..42.

## References

- [FastAPI async guidance](https://fastapi.tiangolo.com/async/)
- [FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)
- [Next.js installation](https://nextjs.org/docs/app/getting-started/installation)
- [Next.js self-hosting](https://nextjs.org/docs/app/guides/self-hosting)
- [Next.js output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output)
- [Node.js release schedule](https://nodejs.org/en/about/previous-releases)
