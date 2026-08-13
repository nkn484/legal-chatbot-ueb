# Nhóm 4 — Dữ liệu văn bản, xử lý và chỉ mục

Áp dụng HR-01 đến HR-22, HR-27, HR-35 đến HR-42.

**Đầu vào chung:** Nhóm 3 đã `PASS`, contract Document/Processing/Index đã duyệt, nguyên tắc cứng và artifact của prompt đứng trước.

## Prompt 04.1 — Document schema và migration

**Mục tiêu duy nhất:** Tạo mô hình dữ liệu vòng đời văn bản.

**Công việc:** Thiết kế `documents`, immutable `document_versions`, metadata pháp lý, source, file manifest, optimistic version và trạng thái. Tạo migration forward/rollback hoặc forward-fix.

**Đầu ra:** ORM/domain model, migration, state table, tests constraints.

**Cổng PASS:** Không ghi đè version; số ký hiệu trùng chỉ cảnh báo; metadata hiệu lực có provenance/người xác nhận.

**Cấm:** OCR, embedding hoặc search trong Document Service.

**Dừng:** Chờ inspect schema.

---

## Prompt 04.2 — Upload và object storage

**Mục tiêu duy nhất:** Nạp file gốc an toàn.

**Công việc:** Streaming/presigned upload; SHA-256; MIME sniffing; size/type allowlist; safe filename; storage key nội bộ; malware-scan hook; duplicate-byte handling.

**Đầu ra:** Upload API/adapter/tests.

**Cổng PASS:** PDF/DOCX/HTML/TXT hợp lệ; extension giả, path traversal, file quá lớn/hỏng bị chặn; API không lộ storage credential/key.

**Cấm:** Đưa file chưa scan vào processing.

**Dừng:** Chờ security review upload.

---

## Prompt 04.3 — Lifecycle và versioning

**Mục tiêu duy nhất:** Thực thi state machine văn bản.

**Công việc:** `UPLOADED → PROCESSING → READY_FOR_REVIEW → PUBLISHED | REJECTED | FAILED`; publish/unpublish/reprocess/new-version; maker-checker tùy cấu hình; audit.

**Đầu ra:** Domain service, APIs, transition tests.

**Cổng PASS:** Transition sai fail; hai publish đồng thời không tạo hai active versions; version mới không tự thay bản đang publish.

**Cấm:** Auto-publish sau extraction.

**Dừng:** Chờ duyệt.

---

## Prompt 04.4 — Outbox và processing request

**Mục tiêu duy nhất:** Phát event xử lý tài liệu tin cậy.

**Công việc:** Transactional outbox cho uploaded/processing-requested/published/unpublished; publisher confirm; retry/DLQ; reconciliation.

**Đầu ra:** Outbox migration, relay, tests crash/restart.

**Cổng PASS:** Commit metadata và event không lệch; duplicate publish không gây side effect lặp.

**Cấm:** Publish event trước commit DB.

**Dừng:** Chờ bằng chứng recovery.

---

## Prompt 04.5 — Processing job engine

**Mục tiêu duy nhất:** Tạo worker/job durable, chưa xử lý nội dung.

**Công việc:** Job/state/stage/attempt/progress; inbox idempotency; retry/backoff/DLQ; cancel/resume/replay; resource/time limits; temp cleanup.

**Đầu ra:** Worker skeleton, job repository, queue adapters, tests.

**Cổng PASS:** Restart không nhân đôi job/artifact; lỗi retryable/permanent tách đúng; progress quan sát được.

**Cấm:** Nhét OCR đồng bộ vào upload request.

**Dừng:** Chờ duyệt job model.

---

## Prompt 04.6 — Trích xuất PDF/DOCX/HTML/TXT

**Mục tiêu duy nhất:** Trích xuất text và layout theo trang/khối.

**Công việc:** Adapter từng định dạng; page/block output; Unicode; password-protected/corrupt handling; HTML sanitize; extractor version/hash.

**Đầu ra:** Extractors, fixtures hợp pháp, accuracy/coverage tests.

**Cổng PASS:** Giữ số trang và heading; lỗi có code redacted; không log nội dung tài liệu.

**Cấm:** Dùng LLM để “sửa” văn bản nguồn.

**Dừng:** Báo hạn chế từng định dạng.

---

## Prompt 04.7 — OCR tiếng Việt

**Mục tiêu duy nhất:** Xử lý trang scan qua adapter OCR thay thế được.

**Công việc:** Detect page thiếu text; OCR page-batch; confidence/coverage; timeout; CPU/RAM limits; version engine/model; preserve page coordinates nếu có.

**Đầu ra:** OCR adapter/config/benchmark/fixtures.

**Cổng PASS:** PDF scan tiếng Việt đo được chất lượng; trang confidence thấp chuyển `NEEDS_REVIEW`; timeout không làm mất job.

**Cấm:** Gắn `SUCCEEDED` khi OCR rỗng/thấp dưới ngưỡng.

**Dừng:** Chờ người dùng duyệt engine/ngưỡng.

---

## Prompt 04.8 — Chuẩn hóa và chunking pháp lý

**Mục tiêu duy nhất:** Tạo chunk bảo toàn cấu trúc pháp lý.

**Công việc:** Xử lý header/footer lặp và whitespace nhưng giữ nguyên nghĩa; nhận diện Chương/Mục/Điều/Khoản/Điểm; fallback 500–900 tokens, overlap 80–150; stable chunk ID/content hash.

**Đầu ra:** Normalizer/chunker, manifest schema, golden fixtures.

**Cổng PASS:** Không tách tiêu đề khỏi nội dung; page/provision path đúng; chạy lặp tạo cùng IDs/hashes.

**Cấm:** Paraphrase nguồn; thực thi instruction trong tài liệu.

**Dừng:** Chờ inspect sample chunks.

---

## Prompt 04.9 — Quality gate và review artifact

**Mục tiêu duy nhất:** Quyết định artifact đủ điều kiện kiểm duyệt hay cần xử lý lại.

**Công việc:** Metrics coverage/confidence/structure/empty/duplicate/injection-risk; report theo trang/chunk; `SUCCEEDED | NEEDS_REVIEW | FAILED`; event completed/failed.

**Đầu ra:** Quality rules/version, report API, tests.

**Cổng PASS:** Ngưỡng cấu hình/versioned; không report PASS khi thiếu page; event không chứa full content/secret.

**Cấm:** Quality service tự publish.

**Dừng:** Chờ duyệt ngưỡng.

---

## Prompt 04.10 — Index schema và Full Text Search

**Mục tiêu duy nhất:** Lập chỉ mục từ khóa trong Index Service.

**Công việc:** Indexed document/chunk; active/version/model fields; PostgreSQL FTS tiếng Việt; allowlisted filters; inbox/outbox; keyword search API.

**Đầu ra:** Migration, indexer, search API, explain/benchmark.

**Cổng PASS:** Exact số ký hiệu/Điều-Khoản tìm được; unpublished không active; service khác không đọc index DB.

**Cấm:** Hybrid fusion hoặc sinh câu trả lời.

**Dừng:** Chờ benchmark.

---

## Prompt 04.11 — Embedding và vector index

**Mục tiêu duy nhất:** Sinh embedding và truy vấn pgvector.

**Công việc:** Embedding adapter; batch/rate-limit/retry/cost metrics; dimension/model version; vector search; partial failure recovery; index activation atomically.

**Đầu ra:** Embedding jobs, pgvector migration/query, tests.

**Cổng PASS:** Count/hash/dimension khớp manifest; duplicate event không tạo vector trùng; 429/timeout resume an toàn.

**Cấm:** Dùng secret của answer Provider ngầm; ghi vector không kèm model version.

**Dừng:** Chờ duyệt model và chi phí.

---

## Prompt 04.12 — Reindex, unpublish và rollback

**Mục tiêu duy nhất:** Quản lý vòng đời index khi dữ liệu/model đổi.

**Công việc:** Index version/alias; reindex song song; atomic switch; deactivate khi unpublish; out-of-order reconciliation; rollback.

**Đầu ra:** Commands/admin API/runbook/tests.

**Cổng PASS:** Unpublish biến mất trong SLA; reindex không downtime ở mức demo; rollback về index hợp lệ.

**Cấm:** Xóa index cũ trước khi candidate index đạt quality check.

**Dừng:** Chờ recovery review.

---

## Prompt 04.13 — Cổng nghiệm thu pipeline dữ liệu

**Mục tiêu duy nhất:** Kiểm tra vertical slice upload → review → publish → index.

**Công việc:** Chạy file text PDF, scan PDF, DOCX, HTML, TXT; duplicate, corrupt, OCR thấp, replay, unpublish/reindex.

**Đầu ra:** `docs/progress/04-data-pipeline-gate.md`, benchmark CPU/RAM/time/page.

**Cổng PASS:** HR-15 và HR-21 chứng minh bằng test; source/page/chunk/hash truy nguyên đầy đủ; không secret/text nguồn trong log mặc định.

**Cấm:** Dùng fixture giả để che lỗi extractor/OCR thực.

**Dừng:** Chỉ đề xuất Prompt 05.1.
