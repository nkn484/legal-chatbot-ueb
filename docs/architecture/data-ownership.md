# Sở hữu dữ liệu theo bounded context (02.1)

## Bất biến áp dụng

Mô hình này áp dụng HR-08..14: bounded context, data ownership riêng, contract versioned, async cho tác vụ dài, outbox/inbox đáng tin cậy, không shared business model và khả năng triển khai độc lập. Mỗi state-owning service owns private persistence/schema/credentials as needed; Gateway has no business DB; stateless service need not have DB. Không cross-service DB, SQL, ORM hay migration; cross-service ID không là foreign key. Object storage phân vùng theo service credential/prefix. Projection chỉ để đọc, không authoritative và rebuildable; event không là shared DB. Chỉ generated contract, telemetry và test utility ổn định có thể dùng chung, không có shared business model package.

Identity cung cấp verified context, nhưng authorization tài nguyên do từng domain service enforce. Audit chỉ ghi/query audit, không authorize. Mỗi owner chịu retention/deletion trong dữ liệu mình sở hữu; consumer phải xử lý revocation/tombstone qua contract bất đồng bộ khi được định nghĩa.

## Capability ownership matrix

| Capability ID | Capability | Single owner | Consumers/notes |
|---|---|---|---|
| CAP-001 | Edge routing | api-gateway | Chỉ route, limit, sanitized error; không orchestration nghiệp vụ |
| CAP-002 | Identity/authentication | identity-service | Cung cấp verified context; domain service tự authorize resource |
| CAP-003 | Audit integrity/retention/query | audit-service | Nhận audit fact async; không synchronous domain write |
| CAP-004 | Legal metadata/version/publish | document-service | Sole authority `PUBLISHED && active` |
| CAP-005 | Original object manifest | document-service | Object hash/ref/retention; grant đọc có kiểm soát |
| CAP-006 | Processing jobs | processing-service | Nhận request async; không publish |
| CAP-007 | Extracted/chunk artifacts | processing-service | Excerpt/page/provision locator canonical |
| CAP-008 | Quality review artifacts | processing-service | Outcome gửi Document bất đồng bộ |
| CAP-009 | Index projections/activation | index-service | FTS Core; vector/embedding chỉ khi duyệt sau |
| CAP-010 | Retrieval/ranking/sufficiency | retrieval-service | Trả evidence IDs/context refs và reason/refusal |
| CAP-011 | Citation validation/rendering | citation-service | Không tin caller/model metadata; độc lập Provider |
| CAP-012 | Conversations/answer/refusal | chat-service | Snapshot bất biến cho Feedback LATER |
| CAP-013 | Provider config/secrets/adapters | provider-service | Secret reference write-only; không answer/citation |
| CAP-014 | Feedback | feedback-service | Raw feedback không là ground truth |
| CAP-015 | Annotation | feedback-service | Thuộc Golden workflow |
| CAP-016 | Golden Answer | feedback-service | Chỉ APPROVED có citation hợp lệ thành Golden fact |
| CAP-017 | Frozen datasets | evaluation-service | Hash, lineage, split, revoke propagation |
| CAP-018 | Evaluation runs/metrics | evaluation-service | Không auto activate/release |
| CAP-019 | Candidates | evaluation-service | Candidate gate, không production activation |
| CAP-020 | Optional training export | evaluation-service | Chỉ metadata export; no auto-training/fine-tuning |

## Service data ownership

| Container | Owned records/data và authoritative facts | Allowed projections/references | Forbidden access |
|---|---|---|---|
| api-gateway | Rate/request policy state và sanitized routing telemetry; không business data | Verified identity context, bounded response | Domain record ownership/orchestration, DB khác |
| identity-service | Users, credentials, sessions, roles, permissions, service identities, key metadata | Subject/resource IDs | Domain resource authorization data, audit ownership |
| audit-service | Append-only audit records, integrity evidence, retention/query state | Audit facts received async | Authorize hay write path synchronous của domain |
| document-service | Documents, immutable Versions, legal metadata/provenance/effect confirmation, publish/active, original manifest/hash/ref/retention | Processing quality/index outcomes | Processing/index DB, mutable overwrite of version |
| processing-service | Jobs, extraction/normalization/chunks, locator, quality/review, derived refs/hashes | Immutable document view/granted original read | Publish/legal truth/Document DB |
| index-service | FTS/vector projections, indexed refs, index version/build/activation | Processing artifacts and Document eligibility through APIs | Legal truth/canonical extracted text |
| retrieval-service | Query normalization, retrieval run/config, ranking/fusion/sufficiency/reason | Index result refs, Document batch eligibility | Index/Document SQL, canonical source metadata |
| provider-service | Provider config, secret references, lifecycle, adapters | Provider IDs/lifecycle facts | Answer/citation/conversation ownership or secret readback |
| citation-service | Validation runs, claim-evidence maps, rendered citation/reason | Document metadata, Processing excerpt, Index context via APIs | Retrieval/Chat calls, Provider dependency, caller/model metadata |
| chat-service | Conversations/sessions, request/answer/refusal snapshot, idempotency, redacted metrics | Retrieval evidence/refusal, Citation render | Service DBs, index/provider secrets, metadata authoring |
| feedback-service | Feedback, annotations, Golden lifecycle | Immutable Chat snapshot, Citation revalidation LATER | Raw feedback/model output as ground truth |
| evaluation-service | Frozen datasets, eval runs/metrics, candidates, training-export metadata | Approved/revoked Golden facts, source revocations, Citation revalidation LATER | Activate Chat/Provider/release or auto-training |

## Quy tắc dữ liệu và điều kiện mở

Các API/event schema, protocol, storage engine, endpoint, field và deployment packaging là `NOT_DECIDED` cho 02.2–02.5, không phải mơ hồ về owner. Dữ liệu active Core không được hấp thụ Provider/Feedback/Evaluation dù các capability này là LATER. `DEC-005` vẫn **OPEN**: Citation độc lập Provider, nhưng cần governance/manifest decision được phê duyệt trước khi claim executable Core path; không thêm Provider vào Core hoặc defer Citation.

Để bảo vệ HR-15..18 và HR-22, Document giữ publish/active và metadata canonical, Processing giữ excerpt canonical, Index giữ context membership projection, Citation validate/render, Chat không tự tạo metadata. Để bảo vệ HR-29..33, feedback/model answer không tự thành ground truth, Golden phải approved và Evaluation không tự train/release.
