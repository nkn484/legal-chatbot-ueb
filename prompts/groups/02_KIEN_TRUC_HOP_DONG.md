# Nhóm 2 — Kiến trúc và hợp đồng

Mọi prompt trong nhóm này áp dụng HR-01 đến HR-14, HR-22, HR-27, HR-41 và HR-42.

**Đầu vào chung:** Phạm vi nhóm 1 đã `PASS`, `00_NGUYEN_TAC_CUNG.md` và mọi artifact đã được duyệt của prompt đứng trước.

## Prompt 02.1 — Chốt bounded contexts và ownership

**Mục tiêu duy nhất:** Chốt ranh giới service và quyền sở hữu dữ liệu.

**Đầu vào:** Phạm vi đã duyệt; inventory.

**Công việc:** Mô tả API Gateway, Identity/Audit, Document, Processing, Index, Retrieval, Provider, Citation, Chat, Feedback/Annotation, Training/Evaluation. Nêu dữ liệu sở hữu, API/event cung cấp và dependency được phép.

**Đầu ra:** `docs/architecture/container-map.md`, `docs/architecture/data-ownership.md`.

**Cổng PASS:** Không cross-service DB; không vòng phụ thuộc đồng bộ; mỗi năng lực có đúng một owner.

**Cấm:** Tạo service theo từng bảng; shared business-model package.

**Dừng:** Chờ duyệt boundaries.

---

## Prompt 02.2 — ADR công nghệ và giao tiếp

**Mục tiêu duy nhất:** Ghi quyết định kiến trúc, chưa viết business code.

**Công việc:** ADR cho REST + RabbitMQ; PostgreSQL; pgvector thuộc Index; MinIO/S3; Redis chỉ cache/rate limit/lock; monorepo/deploy độc lập; FastAPI async; Next.js; OpenTelemetry/Prometheus; OAuth2/OIDC-ready.

**Đầu ra:** Mỗi ADR có context, options, decision, consequences, reconsideration trigger.

**Cổng PASS:** Mọi lựa chọn có trade-off và phương án bị loại; không coi công nghệ là yêu cầu nghiệp vụ.

**Cấm:** Đưa Kafka/Kubernetes/HA vào MUST nếu phạm vi chưa yêu cầu.

**Dừng:** Chờ người dùng duyệt ADR.

---

## Prompt 02.3 — Domain schema và state machine

**Mục tiêu duy nhất:** Định nghĩa schema trung lập công nghệ cho dữ liệu trao đổi.

**Công việc:** Chuẩn hóa Document/Version/Status/Job/Chunk/Index/Retrieval/Chat/GroundedAnswer/Citation/ProviderConfigView/Feedback/GoldenAnswer/Dataset/Evaluation/Candidate. Định nghĩa state transition và invariant.

**Đầu ra:** `contracts/schemas/*.json`, examples success/error/refusal.

**Cổng PASS:** Schema validate; `ProviderConfigView` không có secret; `GroundedAnswer` chỉ nhận chunk IDs, không nhận URL do LLM tạo.

**Cấm:** Gắn schema dùng chung trực tiếp với ORM model nội bộ.

**Dừng:** Xuất danh sách trường còn cần nghiệp vụ xác nhận.

---

## Prompt 02.4 — OpenAPI public và internal

**Mục tiêu duy nhất:** Chốt hợp đồng HTTP v1.

**Công việc:** Viết OpenAPI riêng cho public/admin/internal endpoints; error envelope; pagination/filter; idempotency key; auth scope; request size; timeout semantics.

**Đầu ra:** `contracts/openapi/*.yaml`, examples và lint config.

**Cổng PASS:** Lint đạt; examples validate; không endpoint nào yêu cầu query database service khác; không API trả secret/storage key.

**Cấm:** Triển khai handler nghiệp vụ.

**Dừng:** Chờ inspect endpoint/field.

---

## Prompt 02.5 — AsyncAPI và độ tin cậy event

**Mục tiêu duy nhất:** Chốt event contracts và delivery semantics.

**Công việc:** Định nghĩa event envelope và các event document processing/publish/index/provider/chat/feedback/golden/dataset/evaluation/candidate. Ghi producer, consumer, ordering, retention, retry, DLQ và idempotency key.

**Đầu ra:** `contracts/asyncapi/asyncapi.yaml`, schema/examples, event ownership matrix.

**Cổng PASS:** AsyncAPI lint; duplicate/out-of-order scenarios được mô tả; payload không chứa secret/full document text ngoài nhu cầu.

**Cấm:** Cam kết exactly-once xuyên hệ thống; dùng event như shared database.

**Dừng:** Chờ duyệt.

---

## Prompt 02.6 — Threat model và privacy model

**Mục tiêu duy nhất:** Nhận diện luồng tin cậy và rủi ro trước triển khai.

**Công việc:** STRIDE + OWASP LLM cho upload, auth, Provider SSRF, prompt injection, insecure output, data poisoning, PII, supply chain, admin actions. Phân loại dữ liệu và retention.

**Đầu ra:** `docs/architecture/threat-model.md`, data-flow diagram, risk register với owner/mitigation/test.

**Cổng PASS:** Mỗi rủi ro Critical/High có biện pháp và test ID; secret/PII flow được chỉ ra.

**Cấm:** Ghi chung chung “dùng mã hóa” mà không chỉ vị trí, khóa và trách nhiệm.

**Dừng:** Chờ duyệt risk acceptance.

---

## Prompt 02.7 — Cổng nghiệm thu kiến trúc

**Mục tiêu duy nhất:** Kiểm tra tính nhất quán của toàn bộ artifact nhóm 2.

**Công việc:** Chạy schema/OpenAPI/AsyncAPI lint, compatibility tests; kiểm tra traceability từ REQ tới service/API/event/test; phát hiện dependency cycle và cross-DB.

**Đầu ra:** `docs/progress/02-architecture-gate.md`.

**Cổng PASS:** Không còn breaking inconsistency hoặc blocker security; mọi quyết định mở được người dùng xử lý.

**Cấm:** Sửa contract ngầm trong lúc chạy gate.

**Dừng:** Chỉ đề xuất Prompt 03.1.
