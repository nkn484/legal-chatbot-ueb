# Bản đồ container và bounded context (02.1)

## Phạm vi và trạng thái quyết định

Tài liệu này chốt mô hình logic mặc định cho Prompt 02.1, không chốt đóng gói vật lý, công nghệ, endpoint hay schema. Trạng thái: **PASS_WITH_CONDITIONS_CANDIDATE**. Có đúng 12 bounded context/container logic; Web Chat và Admin Portal là client, còn object store, message broker, cache và DB engine là hạ tầng, không là chủ sở hữu nghiệp vụ.

| Container | Trách nhiệm | Không chịu trách nhiệm | Kích hoạt |
|---|---|---|---|
| api-gateway | Transport routing, truyền verified auth context, rate/request limits và lỗi đã sanitize | Dữ liệu nghiệp vụ, business response composition/aggregation hay điều phối nghiệp vụ | Core |
| identity-service | User, credential, session, role, permission, service identity, key metadata | Quyết định quyền trên tài nguyên miền, audit authorization | Core |
| audit-service | Audit append-only, integrity, retention, query | Authorize, phụ thuộc đồng bộ của luồng ghi nghiệp vụ | Core |
| document-service | Document/Version bất biến, metadata pháp luật, provenance, hiệu lực đã xác nhận, publish/active | Extraction, chunk, index, quyết định publish qua gọi đồng bộ service khác | Core |
| processing-service | Job extraction/normalization/chunk, locator, quality/review, derived refs/hash | Publish hay legal truth | Core |
| index-service | FTS projection, indexed projection, version/build/activation index | Legal truth, canonical extracted text; vector/embedding khi chưa duyệt | Core (FTS) |
| retrieval-service | Normalize query, retrieval run/config, ranking/fusion, sufficiency/reason | Metadata nguồn canonical, truy cập DB service khác | Core |
| provider-service | Provider config, secret reference, lifecycle, adapter | Answer, citation, sở hữu secret của Chat | LATER |
| citation-service | Validation run, claim-evidence map, citation render/reason | Tin metadata caller/model, gọi Retrieval/Chat, phụ thuộc Provider | Core |
| chat-service | Conversation/session, answer/refusal snapshot, extractive assembly, idempotency, redacted metrics | Override insufficiency, DB service khác, index/provider secret, bỏ qua Citation | Core |
| feedback-service | Feedback, annotation, Golden Answer lifecycle | Biến feedback/model answer thô thành ground truth | LATER |
| evaluation-service | Frozen dataset, evaluation run/metric, candidate gate, metadata export training tùy chọn | Activate Chat/Provider/release hay auto-training | LATER |

API capability và event family dưới đây chỉ là mức capability **provisional**; không phải endpoint, protocol hay schema contract. Chúng thuộc Prompt 02.2–02.5 và hiện là `NOT_DECIDED`.

## Provided API and event capabilities

Event family trong bảng này là provisional; tên, schema và protocol cuối thuộc 02.5. API capability chỉ mô tả khả năng, không là endpoint/contract.

| Container | Provided synchronous API capabilities | Publishes event families | Consumes event families | Activation |
|---|---|---|---|---|
| api-gateway | Transport route, verified-context propagation, request/rate policy, sanitized error shaping | None: no business events | None required | Core |
| identity-service | Authentication and verified identity context | Identity/admin lifecycle facts; audit facts | None required | Core |
| audit-service | Audit query | None required | Domain audit facts; identity/admin facts | Core |
| document-service | Document/version lifecycle, canonical legal metadata, original-read grant | Processing requests; publish/unpublish/active facts; source invalidation/revocation | Processing quality/outcomes; index outcomes | Core |
| processing-service | Processing job/artifact/quality view | Processing quality/outcomes; artifacts-ready; audit facts | Processing requests | Core |
| index-service | Search and index-state view | Index outcomes; audit facts | Artifacts-ready; publish/unpublish/active facts | Core (FTS) |
| retrieval-service | Query normalization, evidence context and sufficiency/refusal | Audit facts | None required | Core |
| provider-service | Provider lifecycle and adapters | Provider lifecycle facts; audit facts | None required | LATER |
| citation-service | Citation validation and canonical rendering | Audit facts | Source invalidation/revocation | Core |
| chat-service | Ask, conversation/session and immutable answer/refusal snapshot | Answer snapshot availability; audit facts | None required | Core |
| feedback-service | Feedback intake, annotation and Golden lifecycle | Golden approved/revoked; audit facts | Answer snapshot availability; source invalidation/revocation; citation facts | LATER |
| evaluation-service | Frozen dataset, evaluation and candidate gate | Audit facts | Golden approved/revoked; source invalidation/revocation | LATER |

## Allowed synchronous dependencies

| Caller | Callee | Purpose | Activation |
|---|---|---|---|
| api-gateway | identity-service | Xác thực và lấy verified auth context | Core |
| api-gateway | document-service | Route capability tài liệu | Core |
| api-gateway | chat-service | Route capability hỏi đáp | Core |
| api-gateway | audit-service | Route truy vấn audit, không phải business write path | Core |
| api-gateway | processing-service | Route bounded processing-job query; không business orchestration | Core |
| processing-service | document-service | Controlled original-read grant và immutable metadata view | Core |
| index-service | processing-service | Đọc artifact bất biến | Core |
| index-service | document-service | Kiểm tra publish/active cuối trước index activation, fail closed | Core |
| retrieval-service | index-service | Tìm kiếm projection | Core |
| retrieval-service | document-service | Batch eligibility PUBLISHED+active | Core |
| citation-service | index-service | Xác thực bounded context/index active | Core |
| citation-service | document-service | Xác thực source, publish state, title/number/URL | Core |
| citation-service | processing-service | Lấy excerpt/page/provision canonical locator | Core |
| chat-service | retrieval-service | Evidence và sufficiency/refusal | Core |
| chat-service | citation-service | Chuyển opaque retrieval-context reference bound to request để Citation độc lập validate/render | Core |
| api-gateway | feedback-service | Route feedback capability | LATER |
| api-gateway | evaluation-service | Route evaluation capability | LATER |
| chat-service | provider-service | Gọi Provider API chỉ sau phê duyệt riêng | LATER |
| feedback-service | chat-service | Resolve immutable answer snapshot | LATER |
| feedback-service | citation-service | Revalidate citation | LATER |
| evaluation-service | feedback-service | Đọc Golden facts | LATER |
| evaluation-service | citation-service | Revalidate citation | LATER |

## Chứng minh đồ thị không chu trình

Thứ tự topo canonical do validation sinh (mọi caller đứng trước callee) là: `api-gateway -> identity-service -> audit-service -> evaluation-service -> feedback-service -> chat-service -> retrieval-service -> provider-service -> citation-service -> index-service -> processing-service -> document-service`. Audit là terminal cho route query; không có synchronous call tới Audit để ghi dữ liệu miền.

## Luồng bất đồng bộ

Các family semantic/provisional (schema/name cuối do 02.5 sở hữu) là: Document→Processing processing request; Processing→Document quality/outcome; Processing→Index artifacts-ready; Document→Index publish/unpublish/active facts; Index→Document index outcome; Document→Citation/Feedback/Evaluation source invalidation/revocation; Chat→Feedback answer snapshot availability; Feedback→Evaluation Golden approved/revoked; mọi domain service→Audit audit facts; Identity→Audit identity/admin facts; Provider lifecycle events ở LATER.

Vòng phản hồi bất đồng bộ không tạo synchronous cycle. Thiết kế contract sau này phải dùng outbox/inbox, idempotency, bounded retry và DLQ.

## Luồng Core fail-closed

Chat gọi Retrieval. Retrieval tìm Index rồi thực hiện kiểm tra eligibility theo lô với Document để bảo đảm candidate vẫn `PUBLISHED` và active. Evidence không đủ, mơ hồ hoặc mâu thuẫn dẫn tới refusal và không gọi Provider. Nếu đủ, Retrieval trả evidence ID/context ref, không trả metadata canonical. Chat chỉ chuyển **opaque retrieval-context reference bound to request** cho Citation; Citation độc lập xác thực reference/context đó, không tin raw ID từ Chat, rồi recheck context/index, Document `PUBLISHED`+active và excerpt/canonical locator từ Processing. Race, ID giả, evidence ngoài context hoặc thiếu metadata đều dẫn tới refusal. Document là canonical metadata; Processing là canonical excerpt; Index là context membership; Citation validate/render; Chat không tự tạo metadata.

## Ranh giới logic và triển khai vật lý

Provider, Feedback và Evaluation đã có ownership nhưng runtime capability là LATER, không được gộp data vào service Core. Việc co-host/đóng gói/deploy vật lý **NOT_DECIDED** trong 02.1 và cần ADR đã duyệt; ownership logic vẫn bắt buộc dù sau này cùng host. Không có standalone training-service: feedback-service sở hữu Golden workflow, evaluation-service sở hữu dataset/evaluation/candidate và metadata export fine-tuning tùy chọn; không auto-training/release.

`DEC-005@2` là candidate pending human approval: Citation không phụ thuộc Provider, Provider vẫn LATER, và candidate manifest sequence là `05.4 -> 05.8 -> 05.9`. Chưa có quyết định currently effective hoặc executable Core path được tuyên bố cho đến khi Prompt 02.7 current revision được người dùng phê duyệt. Không thêm Provider vào Core và không defer Citation.

## Phụ thuộc bị cấm

- Không cross-service DB/SQL/ORM, shared business model, shared migration hoặc service-per-table.
- API Gateway owns no business data/orchestration (Gateway no business orchestration), không multi-domain/business aggregation hay business response composition; Audit không authorize.
- Document không gọi Processing/Index đồng bộ để quyết định publish; Processing không publish; Index không giữ legal truth.
- Retrieval không gọi DB trực tiếp; Citation không gọi Retrieval/Chat và độc lập kiến trúc với Provider.
- Chat không override insufficiency, không bypass Citation, không sở hữu provider secret; Provider không sở hữu answer/citation.

## Tham chiếu ngoài

- [Microsoft: data considerations for microservices](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/data-sovereignty-per-microservice)
- [Microsoft: API gateways](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/design-patterns-api-gateway)
- [Microsoft: event-driven architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven)
- [microservices.io: database per service](https://microservices.io/patterns/data/database-per-service.html), [API Gateway](https://microservices.io/patterns/apigateway.html), [transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [AsyncAPI 3.0 specification](https://www.asyncapi.com/docs/reference/specification/v3.0.0)
