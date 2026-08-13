# ADR-002: Persistence, object storage và cache

- Status: **PROPOSED**
- Date: 2026-08-13

ADR này chỉ trở thành ACCEPTED thông qua phê duyệt của con người cho Prompt 02.2; bản thân tài liệu không cho phép triển khai.

## Context

Ownership của 02.1 giữ nguyên: PostgreSQL không được làm shared business database; Document giữ original manifest, Processing giữ derived artifacts, Index giữ FTS projection. Core là local/demo FTS minimum; semantic retrieval chưa được duyệt và DEC-005 OPEN.

## Options considered

1. **Shared database:** đơn giản cho demo, nhưng phá ownership, deploy độc lập và tạo cross-service coupling.
2. **PostgreSQL database-per-service:** transaction/constraint mạnh và cô lập authority, với chi phí quản trị nhiều logical database/role.
3. **Alternate specialized database:** hữu ích khi workload được chứng minh, nhưng tăng công nghệ trước khi có evidence Core.
4. **PostgreSQL FTS + optional pgvector:** cung cấp FTS Core và lộ trình semantic trong owner Index, nhưng extension/recall phải được xác minh.
5. **Dedicated vector DB:** có thể chuyên cho vector scale, nhưng không cần thiết cho FTS Core hiện tại.
6. **DB BLOB/filesystem/S3-compatible object storage:** BLOB đơn giản nhưng làm database phình; filesystem cục bộ thiếu portable API; S3-compatible object storage phân tách byte object và manifest authority.
7. **Redis authoritative hoặc auxiliary:** authoritative làm correctness phụ thuộc cache; auxiliary hỗ trợ TTL cache/rate limit/advisory coordination mà PostgreSQL vẫn là truth.

## Decision

Mỗi state-owning service có **own PostgreSQL database** riêng và credentials/role riêng. Schema chỉ là tổ chức nội bộ bên trong PostgreSQL database của chính service đó, không bao giờ là lựa chọn thay thế database isolation. Một local/demo PostgreSQL instance có thể host nhiều database được đặt tên riêng biệt, nhưng no shared business database/schema, no cross-service role, no cross-service SQL, no cross-service FK, no cross-service ORM, no cross-service migration hoặc no cross-service connection credentials. PostgreSQL là authoritative source of truth.

Index sở hữu FTS. pgvector extension/tables/migrations/embedding/index lifecycle chỉ do Index sở hữu và là LATER/conditional: chỉ activate sau nhu cầu semantic retrieval được phê duyệt và recall/latency trên frozen fixture được đo. Không có dedicated vector DB trong Core.

Dùng S3-compatible object API. Document sở hữu original object manifest/hash/ref; Processing sở hữu derived artifacts. Key immutable, content-addressed/versioned; policy credential bucket/prefix tách theo service. DB manifest commit là authoritative, upload object đơn lẻ không publish; cần verify checksum/size và quarantine/orphan cleanup. MinIO chỉ là local/reference candidate có điều kiện, không mandatory production: maintenance/distribution/license status và image provenance/security support cần legal/procurement/security review rõ ràng; alternatives S3-compatible được phép sau API compatibility review. ADR này không đưa legal advice.

Redis chỉ cho TTL cache, rate limiting và advisory coordination lock; không là truth cho publish, legal, audit, auth, idempotency, job hay workflow. Transition nhạy correctness dùng PostgreSQL constraints/transactions/optimistic revision; Redis degradation không được bypass auth/publish/citation/rate policy và security-relevant failure fail closed. Nếu dùng lock: lease ngắn, token duy nhất, release kiểm ownership, timeout, idempotency/fencing khi protected resource hỗ trợ. Exact Redis distribution/version cần license review; compatible alternative có thể chọn sau test.

## Consequences

### Positive

- Cô lập data authority, bảo toàn HR-09 và cho Index FTS Core rõ owner.
- Object manifest có hash/verification tăng traceability, còn Redis không làm mất correctness khi hỏng.

### Negative/trade-offs

- Cần vận hành role/database/migration riêng và reconciliation object orphan.
- pgvector, MinIO candidate và Redis distribution chưa thể coi là approved implementation hay license-suitable.

## Rejected options

- Shared DB, cross-service FK và shared migration bị từ chối vì phá private ownership.
- Dedicated vector DB bị từ chối cho Core FTS minimum; có thể xem lại khi evidence scale/semantic retrieval tồn tại.
- Redis authoritative bị từ chối vì cache/lock không được là source of truth.

## Constraints and guardrails

PostgreSQL support/version policy, exact extensions, image versions và Redis/MinIO distribution chỉ chọn sau supported-combination, security/license review, digest và lockfile. Database-per-service bắt buộc; no shared business database/schema, no cross-service connection credentials và không shared business model. Kafka, Kubernetes và HA không là Core MUST. DEC-005 OPEN và không được stack này giải quyết; không claim executable Citation path. Endpoint/event schema/field chính xác để prompt contract sau.

## Reconsideration triggers

Xem xét vector DB hoặc activate pgvector khi semantic need được phê duyệt và frozen-fixture recall/latency được đo. Xem xét object/cache implementation khác khi compatibility, durability, security hoặc license/procurement review không đạt.

## Related boundaries and rules

Giữ 12 context, DAG 02.1 và data-ownership: Document/Processing/Index là owner như đã phê duyệt; projection rebuildable, event không là shared DB. Áp dụng HR-08..14, HR-15..22, HR-23, HR-36..42.

## References

- [PostgreSQL versioning policy](https://www.postgresql.org/support/versioning/)
- [PostgreSQL full text search](https://www.postgresql.org/docs/current/textsearch.html)
- [PostgreSQL license](https://www.postgresql.org/about/licence/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Amazon S3 API reference](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)
- [MinIO repository](https://github.com/minio/minio)
- [MinIO documentation](https://docs.min.io/)
- [MinIO license](https://github.com/minio/minio/blob/master/LICENSE)
- [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
- [Redis distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
- [Redis licensing](https://redis.io/legal/licenses/)
