# Quyết định HTTP API v1 — Prompt 02.4

## Quyết định và biên giới

API v1 dùng OpenAPI 3.1.1, JSON Schema dialect 3.1 và chỉ server tương đối `/`; deployment inject base path. Không contract nào khẳng định domain, IdP hay URL nguồn. `public-v1.yaml` có một route công khai; `admin-v1.yaml` là route gateway-facing có xác thực. Gateway chỉ route/auth propagation/rate-limit/sanitized error, không aggregate và không đọc database.

Mỗi contract internal là API của **một owner service**, không có “internal gateway” dùng chung. `x-ueb-data-access: OWNER_SERVICE_ONLY` buộc owner kiểm tra resource authorization và sở hữu dữ liệu.

| Audience | Contract | Owner operation |
|---|---|---|
| PUBLIC | `public-v1.yaml` | chat-service |
| ADMIN | `admin-v1.yaml` | document-service, processing-service, audit-service |
| INTERNAL | `internal-document-v1.yaml` | document-service |
| INTERNAL | `internal-processing-v1.yaml` | processing-service |
| INTERNAL | `internal-index-v1.yaml` | index-service |
| INTERNAL | `internal-retrieval-v1.yaml` | retrieval-service |
| INTERNAL | `internal-citation-v1.yaml` | citation-service |

## Endpoint inventory và DAG

| Bề mặt | Endpoint / operation |
|---|---|
| Public | `POST /v1/questions` — `askQuestion` |
| Admin document | create/list/get document, get version, record review, publish, unpublish |
| Admin process/audit | get processing job; list audit records |
| Internal document | metadata/content, eligibility batch, canonical metadata batch |
| Internal processing/index | chunks batch; search; retrieval-context validate |
| Internal retrieval/citation | retrieval run; citation validation |

Luồng logic bị giới hạn: `chat → retrieval → index/document/processing → citation → chat public rendering`. Citation canonical được citation-service trả về; chat-service chỉ công bố claim/citation an toàn. Publish không đồng bộ gọi Processing hoặc Index. Upload chỉ tạo request/job `QUEUED`, không là bằng chứng an toàn, publish hoặc hiệu lực pháp luật.

## Auth, lỗi và cache

Public question ghi rõ `security: []`. Mọi admin/internal operation dùng `BearerAuth`, có non-empty `x-ueb-required-scopes`; không có OAuth/OIDC discovery URL hoặc role header được tin cậy. Owner service vẫn kiểm tra resource authorization; resource không được phép có thể là 404 không enumeration.

Lỗi 4xx/5xx dùng `application/problem+json` theo RFC 9457: `type` URI tuyệt đối, title/status, safe detail, opaque instance, code, correlation_id và optional JSON Pointer errors. Không trả stack, SQL, raw payload, internal ID hoặc secret. Response dynamic/auth dùng `Cache-Control: no-store`. `X-Request-Id` là correlation opaque; `Retry-After` chỉ có transient 429/503 đã document.

## Cursor, idempotency, size và deadline

Cursor opaque tối đa 256 ký tự; mỗi endpoint có stable sort cố định. `limit` 1..100/default 25, audit default 50. Page bắt buộc `items`, `next_cursor` nullable và `has_more`; không có offset, arbitrary query hoặc sort.

`Idempotency-Key` là **quy ước dự án, không phải RFC**: ASCII 8..128, scope=`principal/session + operationId + key`, TTL 24 giờ, canonical request fingerprint. Cùng request hoàn tất replay response gốc kèm `Idempotency-Replayed: true`; in-flight là 409, fingerprint khác là 422, thiếu/sai là 400. Ambiguous timeout chỉ retry cùng key.

`x-ueb-request-max-bytes` là octet sau transfer-coding và trước decompression; upload còn có `x-ueb-decompressed-max-bytes`. `x-ueb-timeout-ms` là response-wait budget, không chứng minh cancellation. 408 là incomplete request và 504 là downstream wait timeout. Internal bắt buộc `X-Request-Deadline-At`; deadline malformed/expired là 400 và service không được kéo dài deadline.

## Bảo vệ RAG và các loại trừ

Question input chỉ có question/conversation/locale, không nhận chunk, context, retrieval, citation, source hay provider fields. Public ANSWER có claim liên kết citation; validator kiểm tra fixture có ID liên kết. Thiếu/ambiguous/conflict/inactive/citation-invalid evidence dùng `200 REFUSAL`, không answer suy đoán.

Public `response_ref`, `claim_ref` và `citation_ref` là reference trình bày ngắn hạn của API, không phải ID service hay persistence. Validator fail-closed kiểm tra ref duy nhất, mọi claim phải trỏ citation tồn tại, mỗi citation phải map ngược đúng claim và không có citation bỏ phí. REFUSAL dùng đúng schema 02.3 Common Refusal, gồm code controlled và `retryable`.

Internal Index, Retrieval và Citation mang `request_binding_id`. Request/response fixtures chứng minh binding nhất quán; context stale/foreign/injected bị owner từ chối. Retrieval bọc nguyên `RetrievalRun` 02.3 nên SUFFICIENT cần evidence và không refusal; Citation chỉ nhận GroundedAnswer ANSWER cùng context, trả VALID citations không rỗng hoặc REFUSAL. Chunk là projection exact của Processing Chunk; locator projection giữ đủ page/article/clause/point/character offsets.

Citation semantic gate còn kiểm tra completeness: mỗi grounded claim phải có ít nhất một citation VALID; không được có citation cho claim ngoài request; `grounded_answer_id`, context, request binding và chunk lineage phải khớp. Chunk citation không rỗng và là tập con chunk của claim. REFUSAL chỉ có Common Refusal an toàn, không có citations.

Không có endpoint source catalog, source-system, connector, Provider, Feedback, Evaluation hay training. Upload multipart chỉ nhận đúng một PDF và không có `source_system_id`: manual upload không khẳng định SourceDocumentRef/provenance; declared/detected MIME, signature, malware và quarantine là runtime `NOT_MEASURED`. DEC-005 vẫn mở, connector `NOT_IMPLEMENTED` và allowlist trống; do đó không có thực thi nguồn. API view không có secret/credential, storage object, presigned URL, manifest reference hay location.

## Open fields và đo lường còn thiếu

Contract là bounded design artifact. Runtime token verification, scopes/resource authorization, idempotency store/TTL/fingerprint, upload content security, actual byte/decompression enforcement, timeout/cancellation/deadline propagation, rate-limit/cache và service networking là `NOT_MEASURED`. Custom validator không thay thế OAS meta-validator đầy đủ; Redocly/Spectral/openapi-spec-validator không có trong môi trường.

## Tham chiếu chính thức

- OpenAPI Specification 3.1.1: <https://spec.openapis.org/oas/v3.1.1.html>
- JSON Schema 2020-12: <https://json-schema.org/draft/2020-12/json-schema-core>
- RFC 9457 Problem Details: <https://www.rfc-editor.org/rfc/rfc9457>
- RFC 9110 HTTP Semantics: <https://www.rfc-editor.org/rfc/rfc9110>
