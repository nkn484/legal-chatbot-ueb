# Cổng kết nối nguồn — Revision 2 Prompt 02.3

## Mục đích và owner

`document-service` sở hữu registry nguồn và các DTO exchange technology-neutral trong `source-connector-port.schema.json`. Đây không phải API/event, adapter, connector implementation hay quyết định legal authority.

Port có ba capability khái niệm: `discover_changes`, `fetch_document`, `validate_source_availability`. Các capability chỉ tạo/đọc provenance `SourceDocumentRef`; không có connector, endpoint hay adapter cho VNU/UEB.

## Registry cố định và rollout

| Nguồn | Lifecycle | Phase | Priority | Transport/endpoint | Trạng thái connector |
|---|---|---:|---:|---|---|
| VBQPPL | ACTIVE registry | CORE | 1 | `SOAP_ASMX`; `https://ws.vbpl.vn/vbqppl.asmx` | `NOT_IMPLEMENTED`; không adapter/fetch success |
| VNU | PLANNED | LATER | 2 | Không endpoint, `NOT_CONFIGURED` | `NOT_IMPLEMENTED` |
| UEB | PLANNED | LATER | 3 | Không endpoint, `NOT_CONFIGURED` | `NOT_IMPLEMENTED` |

`rollout_priority` chỉ là thứ tự rollout vận hành. Nó không phải hierarchy/effect/applicability pháp lý, credibility nguồn, retrieval rank hay conflict resolution.

`SourceSystem` là lifecycle generic: mọi trạng thái `ACTIVE`, `PLANNED`, `DISABLED`, `RETIRED` đều biểu diễn được với source ID/priority đã gắn cố định. Catalog hiện tại là snapshot riêng, đóng thứ tự `VBQPPL`, `VNU`, `UEB` và current fields bằng `prefixItems`; vì vậy không biến lifecycle generic thành claim rằng trạng thái hiện tại đã đổi.

## Read-only fail-closed

Chỉ read operation có thể được cho phép cho VBQPPL. WSDL inspection là `NOT_MEASURED`: HTTPS TLS hostname mismatch, HTTP trả `404`. Vì vậy operation allowlist hiện rỗng với `PENDING_VERIFICATION` và `DENY_BY_DEFAULT`; không SOAP call nào được phép. `CREATE`, `UPDATE`, `REMOVE`, `DELETE`, `WRITE`, mọi mutation tương đương và unknown operation đều bị từ chối. Không suy diễn hay đặt tên SOAP operation.

Credential runtime là secret reference được resolve ngoài exchange schema, fixture, log, source code và port payload; không read-back. Future implementation phải thực hiện SSRF URL/redirect/DNS checks, timeout/rate/cursor policy, TLS/WSDL verification và allowlist read operation đã được duyệt. Không có connector thực thi trong Prompt 02.3.

## Provenance và publish gate

`fetch_document` có thể tạo `SourceDocumentRef`; Version chỉ bắt buộc ref đó khi `ingestion_origin=SOURCE_FETCH`, còn `UPLOAD` cấm ref. Schema này chỉ biểu diễn future fetched-reference shape: chưa có valid fetched `SourceDocumentRef` fixture vì WSDL/response/document URL semantics là `NOT_MEASURED`, port `NOT_IMPLEMENTED` và allowlist rỗng. SOAP endpoint chỉ là registry endpoint và schema **cấm** dùng nó làm `source_document_url`. Fetch không tự `PUBLISHED`, không active tài liệu và không xác nhận legal effect. Human review, publish và active gate của Document vẫn là authority fail-closed độc lập. Không fixture nào đặt fake URL hoặc fake connector cho VNU/UEB.
