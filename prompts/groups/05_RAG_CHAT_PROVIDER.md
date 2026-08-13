# Nhóm 5 — Retrieval, Provider, Citation và Chat

Áp dụng HR-01 đến HR-28 và HR-35 đến HR-42. HR-15 đến HR-18, HR-23, HR-25 và HR-26 là blocker.

**Đầu vào chung:** Nhóm 4 đã `PASS`, contract Retrieval/Provider/Citation/Chat đã duyệt, nguyên tắc cứng và artifact của prompt đứng trước.

## Prompt 05.1 — Retrieval contract và query normalization

**Mục tiêu duy nhất:** Chốt request/response của Retrieval Service.

**Công việc:** Giữ câu gốc; normalize không mất số ký hiệu/Điều/Khoản/Điểm; allowlisted filters; access context; response chứa raw/fused/rerank scores, versions, freshness, sufficiency/reason codes.

**Đầu ra:** Contract implementation skeleton và tests validation.

**Cổng PASS:** Client không ép lấy unpublished/unauthorized; query length/filter cardinality bị giới hạn.

**Cấm:** Gọi LLM sinh câu trả lời.

**Dừng:** Chờ inspect contract.

---

## Prompt 05.2 — Hybrid fusion

**Mục tiêu duy nhất:** Hợp nhất keyword và vector results một cách tái lập.

**Công việc:** Lấy top-N hai nhánh; deduplicate chunk/content hash; Reciprocal Rank Fusion; source diversity; context budget; lưu strategy/config/index version.

**Đầu ra:** Fusion engine, config schema, unit/evaluation fixtures.

**Cổng PASS:** Cùng input/version cho cùng ordering; unpublished/unauthorized bị loại; exact identifier không bị semantic result lấn át vô lý.

**Cấm:** Chỉ dùng một cosine threshold làm toàn bộ chính sách.

**Dừng:** Chờ benchmark Recall@K/MRR/nDCG.

---

## Prompt 05.3 — Reranker và fallback

**Mục tiêu duy nhất:** Thêm rerank có timeout và fallback deterministic.

**Công việc:** Adapter reranker; rate/cost/timeout; input minimization; fallback về fusion; versioned scores; circuit breaker.

**Đầu ra:** Adapter/tests/benchmark latency-quality.

**Cổng PASS:** Reranker timeout/429 không làm hỏng retrieval; fallback tái lập; không gửi secret/metadata dư thừa.

**Cấm:** Để reranker tự thay access/publish filters.

**Dừng:** Chờ quyết định bật/tắt mặc định.

---

## Prompt 05.4 — Evidence sufficiency

**Mục tiêu duy nhất:** Xác định khi nào đủ căn cứ để trả lời.

**Công việc:** Rules cho exact identifier, score/margin, coverage, independent sources, conflicting scope/validity, access-filtered; reason codes `NO_MATCH`, `LOW_SCORE`, `INSUFFICIENT_COVERAGE`, `CONFLICTING_SOURCES`, `ACCESS_FILTERED`.

**Đầu ra:** Policy/version/config, tests và threshold-tuning report.

**Cổng PASS:** Query ngoài kho/mơ hồ/mâu thuẫn trả insufficient đúng; không đủ căn cứ không kích hoạt answer model.

**Cấm:** Dùng confidence tự khai của LLM.

**Dừng:** Chờ người dùng duyệt threshold.

---

## Prompt 05.5 — Provider configuration và secret

**Mục tiêu duy nhất:** Lưu cấu hình Provider an toàn, chưa gọi inference.

**Công việc:** Config draft/validated/active/disabled; Base URL/endpoint/model/timeout/retry/temperature/max tokens/RPM/TPM; secret reference; write-only API key; history/version.

**Đầu ra:** Provider schema/migration/APIs/tests.

**Cổng PASS:** Response/DB config không có plaintext key; update không kèm key giữ secret cũ; rotate/delete rõ ràng.

**Cấm:** Log/repr/audit secret; nhiều answer Provider ACTIVE.

**Dừng:** Chờ schema review.

---

## Prompt 05.6 — Validate, activate và rollback Provider

**Mục tiêu duy nhất:** Thực thi vòng đời cấu hình Provider.

**Công việc:** SSRF-safe URL validation/DNS; health check và real minimal request; transactional activation/lock; cache refresh; rollback; audit; normalized errors.

**Đầu ra:** Lifecycle service/tests 401/403/404/429/5xx/timeout/invalid schema.

**Cổng PASS:** Chỉ validated config active; hai activation đồng thời vẫn một ACTIVE; localhost/private/metadata/redirect bị chặn.

**Cấm:** Kích hoạt khi chỉ TCP health thành công nhưng inference thất bại.

**Dừng:** Chờ security review.

---

## Prompt 05.7 — Provider Gateway adapters

**Mục tiêu duy nhất:** Chuẩn hóa lời gọi model qua interface ổn định.

**Công việc:** OpenAI-compatible `/responses`; optional `/chat/completions`; structured output parser; token/cost; timeout/retry/circuit breaker; error mapping; request budget.

**Đầu ra:** Adapters, mock server contract tests, metrics.

**Cổng PASS:** 401/429/timeout/5xx/schema error chuẩn hóa; retry chỉ idempotent/transient; Chat Service không biết SDK cụ thể.

**Cấm:** Log full prompt/context; retry vô hạn.

**Dừng:** Chờ live test riêng nếu có credential.

---

## Prompt 05.8 — Citation Service

**Mục tiêu duy nhất:** Xác minh citation và dựng nguồn canonical.

**Công việc:** Validate chunk ID thuộc context/index active/published; claim-evidence mapping; excerpt nằm trong canonical chunk; lấy metadata từ source service; handle unpublish race.

**Đầu ra:** Citation APIs, validator/tests, reason codes.

**Cổng PASS:** Fake/non-context/unpublished citation bị chặn; URL/title/number/page không lấy từ model; mọi conclusion claim có evidence.

**Cấm:** Cho LLM tự tạo/sửa metadata nguồn.

**Dừng:** Chờ inspect failure policy.

---

## Prompt 05.9 — Prompt registry và input/output guardrails

**Mục tiêu duy nhất:** Quản lý template và guardrails có version.

**Công việc:** Registry ID/version/hash/status; only-approved activation; input length/scope/injection classification; document-as-data delimiter; output JSON schema; repair tối đa một lần; redaction policy.

**Đầu ra:** Prompt registry/guard modules/tests/red-team fixtures.

**Cổng PASS:** Instruction trong document không được thực thi; model không được yêu cầu system prompt/secret; invalid output không đi thẳng tới UI.

**Cấm:** Sửa prompt production không qua evaluation/approval.

**Dừng:** Chờ duyệt template.

---

## Prompt 05.10 — Chat Orchestrator

**Mục tiêu duy nhất:** Điều phối câu hỏi thành GroundedAnswer.

**Công việc:** Validate → guard → retrieve → sufficiency → build minimal context → Provider → parse → Citation → one repair → confidence rule → persist metrics/event. Có idempotency và timeout budget.

**Đầu ra:** Chat Service code/tests/sequence diagram.

**Cổng PASS:** Không đủ evidence không gọi model; provider/citation lỗi có graceful response; output gồm conclusion/analysis/actions/citations/confidence/human-review/freshness/version.

**Cấm:** Tư vấn pháp lý cuối cùng; tự suy luận hiệu lực; bypass Citation Service.

**Dừng:** Chờ inspect vertical slice.

---

## Prompt 05.11 — Privacy và conversation lifecycle

**Mục tiêu duy nhất:** Kiểm soát dữ liệu hội thoại.

**Công việc:** PII detection/redaction trước Provider; retention; export/delete; restricted debug logging; prompt/context artifact access; least-data policy.

**Đầu ra:** Policy/code/tests/audit mapping.

**Cổng PASS:** Secret/PII canary không vào Provider/log/trace trái policy; delete/export có authorization và audit.

**Cấm:** Mặc định lưu full prompt/context vô thời hạn.

**Dừng:** Chờ privacy review.

---

## Prompt 05.12 — Cổng nghiệm thu RAG/Chat

**Mục tiêu duy nhất:** Kiểm tra Retrieval → Provider → Citation → Answer.

**Công việc:** Test một nguồn, nhiều nguồn, mâu thuẫn, ngoài kho, prompt injection, fake citation, unpublish race, Provider failures, 20–30 concurrent demo sessions.

**Đầu ra:** `docs/progress/05-rag-chat-gate.md`.

**Cổng PASS:** 100% conclusion có canonical citation hoặc refusal; HR-15–18/23/25/26 có test; P95 được đo, không suy đoán.

**Cấm:** Giảm ngưỡng để biến test fail thành PASS.

**Dừng:** Chỉ đề xuất Prompt 06.1.
