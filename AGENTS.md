# AGENTS.md — Chatbot Pháp luật

## 1. Phạm vi áp dụng

Đây là chỉ dẫn bắt buộc cho mọi agent, subagent và phiên OpenCode hoạt động trong repository này. Dự án xây dựng Chatbot Pháp luật theo kiến trúc microservice, RAG có kiểm chứng nguồn và hệ thống cải thiện câu trả lời có Human-in-the-loop.

Thứ tự ưu tiên khi có xung đột:

`Bảo mật → Toàn vẹn nguồn/citation → Đúng nghiệp vụ → Độ tin cậy → Truy vết → Hiệu năng → Chi phí → Tiện triển khai`.

## 2. Nguồn chỉ dẫn

Trước khi thực hiện một command `prompt-*`, phải đọc:

1. `AGENTS.md` này.
2. `prompts/00_HARD_RULES.md`.
3. Kết quả `python scripts/prompt_gate.py context <PROMPT_ID>`.
4. Các contract, ADR và artifact đã được duyệt mà command chỉ định.

Không tự suy diễn yêu cầu từ prompt sau hoặc từ mã nguồn chưa được duyệt.

## 3. Mười hai BLOCKER bất biến

1. Chỉ chạy đúng một Prompt ID do người dùng gọi; không tự chuyển prompt.
2. Không viết business code trước khi contract/ADR liên quan đã được duyệt.
3. Chỉ tài liệu/phiên bản `PUBLISHED` và active được retrieval.
4. LLM chỉ trả ID; metadata citation phải lấy từ nguồn canonical của backend.
5. Thiếu evidence phải refusal; không hạ ngưỡng để biến lỗi thành PASS.
6. Mỗi microservice sở hữu dữ liệu; cấm truy cập trực tiếp database của service khác.
7. Không hardcode, đọc ngược, in hoặc ghi log secret/API key/token/mật khẩu.
8. Provider URL phải chống SSRF; cấm loopback, private/link-local và metadata endpoint.
9. Feedback/model answer không tự trở thành ground truth; chỉ Golden Answer đã duyệt được vào dataset.
10. Không tự fine-tune, gọi dịch vụ tốn phí hoặc release candidate khi chưa có phê duyệt riêng.
11. Không ghi `PASS` nếu thiếu bằng chứng chạy thật; dùng `BLOCKED` hoặc nêu rõ `NOT_MEASURED`.
12. Không xóa/hoàn tác thay đổi ngoài phạm vi; cấm lệnh phá hủy và cấm tự push/deploy production.

Vi phạm một BLOCKER phải dừng và báo `FAIL` hoặc `BLOCKED`.

## 4. Giao thức thực thi một prompt

1. Chạy `python scripts/prompt_gate.py check <PROMPT_ID>`; nếu không đủ điều kiện thì dừng.
2. Chạy `python scripts/prompt_gate.py start <PROMPT_ID>`.
3. Ghi ảnh chụp `git status --short`; không sửa thay đổi có sẵn của người dùng.
4. Orchestrator lập dependency graph chỉ bên trong prompt hiện tại.
5. Mỗi subtask phải ghi rõ: mục tiêu, file/search scope, quyền sửa, đầu ra, validation và điều cấm.
6. Agent ghi file phải có `write_scope` không chồng lấn. Mặc định chỉ một writer hoạt động tại một thời điểm.
7. Chạy kiểm thử phù hợp và tạo `docs/progress/<PROMPT_ID>.md` theo template.
8. Chạy `python scripts/prompt_gate.py submit <PROMPT_ID> --report ... --evidence ...`.
9. Dừng ở `AWAITING_APPROVAL`. Chỉ người dùng chạy lệnh duyệt ngoài OpenCode.

Agent bị cấm chạy `approve`, `reject`, `defer` hoặc sửa trực tiếp `.agent-run/prompt-state.json`.

## 5. Điều phối OMO-slim

- **Orchestrator:** lập kế hoạch, giao việc, theo dõi ownership, hợp nhất kết quả và kiểm chứng cuối. Không mặc định trực tiếp triển khai.
- **Explorer:** khảo sát repository, tìm file/pattern/dependency; chỉ đọc.
- **Librarian:** tra cứu tài liệu chính thức, hành vi theo phiên bản và license; chỉ đọc.
- **Oracle:** kiến trúc, trade-off, threat review, debug strategy và code review rủi ro cao; chỉ đọc.
- **Council:** quyết định có nhiều phương án khó đảo ngược; không dùng cho công việc thường lệ.
- **Fixer:** triển khai backend/infra/test trong phạm vi file được giao.
- **Designer:** thiết kế và triển khai UI/UX trong `apps/`; không sửa backend hoặc contract.
- **Observer:** phân tích hình ảnh/PDF/diagram khi được cấu hình; không sửa file.

Có thể chạy song song Explorer/Librarian/Oracle/Council read-only. Không chạy song song hai writer trên cùng file, migration, contract, shared package hoặc thư mục giao nhau.

## 6. Ranh giới kiến trúc mặc định

- `services/api-gateway/`: routing, auth propagation, rate limit và sanitized error; không chứa business orchestration.
- `services/identity-service/`: authentication, user, role và service identity.
- `services/audit-service/`: audit append-only, truy vấn audit và retention.
- `services/document-service/`: metadata, version, publish lifecycle và upload reference.
- `services/processing-service/`: extraction, OCR, normalization, chunking và quality gate.
- `services/index-service/`: FTS, embedding, pgvector và vòng đời index.
- `services/retrieval-service/`: query normalization, hybrid fusion, rerank và sufficiency.
- `services/provider-service/`: provider config, secret reference, lifecycle và gateway adapter.
- `services/citation-service/`: citation validation và canonical source rendering.
- `services/chat-service/`: orchestration hỏi đáp; không sở hữu index hoặc provider secret.
- `services/feedback-service/`: feedback, annotation task và Golden Answer workflow.
- `services/evaluation-service/`: dataset registry, evaluation job và candidate gate.
- `apps/web-chat/`, `apps/admin-portal/`: giao diện; chỉ dùng API/contract được duyệt.

Thay đổi boundary phải tạo ADR đề xuất và chờ người dùng duyệt.

## 7. Quy chuẩn mã và dữ liệu

- Python production: type hints, Pydantic, async I/O khi phù hợp, structured logging, error handling, graceful shutdown.
- API/event contract phải versioned và có example/compatibility test.
- Tác vụ dài dùng queue; event quan trọng dùng Outbox/Inbox, idempotency, retry giới hạn và DLQ.
- Dependency phải pin version; Critical/High từ security scan không được bỏ qua ngầm.
- Không log toàn bộ prompt/context mặc định; redact PII và secret trước Provider/training.
- Tài liệu, chunk, dataset frozen và Golden Answer đã duyệt là bất biến, có hash và lineage.

## 8. Git và an toàn thay đổi

- Luôn kiểm tra working tree trước và sau khi sửa.
- Không reset, clean, force push, rewrite history, tự merge hoặc tự tạo release.
- Không commit nếu command không yêu cầu hoặc người dùng chưa cho phép.
- Không sửa file ngoài `write_scope`; nếu bắt buộc, dừng và xin mở rộng phạm vi.
- Không dùng kết quả của prompt sau để hợp thức hóa thiếu sót của prompt hiện tại.

## 9. Báo cáo bắt buộc

`docs/progress/<PROMPT_ID>.md` phải có:

1. Trạng thái đề xuất: `PASS_CANDIDATE | PASS_WITH_CONDITIONS_CANDIDATE | BLOCKED | FAIL`.
2. File/service/contract/migration đã thay đổi.
3. Lệnh kiểm thử và kết quả thực tế.
4. Đối chiếu mã HR và BLOCKER.
5. Sai lệch, test chưa chạy, rủi ro và điều kiện còn lại.
6. Đề xuất prompt tiếp theo, nhưng tuyệt đối không chạy.
