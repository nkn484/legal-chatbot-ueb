# Tiêu chí nghiệm thu Core Demo v1

## Cách dùng trạng thái

Các tiêu chí dưới đây là tiêu chí sản phẩm tương lai, trừ phần scope-lock của Prompt 01.2. Vì chưa có product implementation hay phép đo, trạng thái hiện tại của toàn bộ tiêu chí sản phẩm là `NOT_MEASURED`, không phải `PASS`.

| AC | REQ | Ưu tiên | Tiêu chí nghiệm thu tương lai | Trạng thái hiện tại |
|---|---|---|---|---|
| AC-001 | REQ-SCP-001 | MUST | Given câu hỏi tiếng Việt trong/ngoài miền, When hệ thống xử lý, Then chỉ phục vụ phạm vi Giáo dục đại học Việt Nam và từ chối có cấu trúc khi ngoài phạm vi. | NOT_MEASURED |
| AC-002 | REQ-USR-001 | MUST | Given người dùng demo, When hỏi đáp, Then không cần self-registration/SSO và không có tenant khác được tạo hoặc chọn. | NOT_MEASURED |
| AC-003 | REQ-USR-002 | MUST | Given chức năng quản trị corpus demo, When truy cập bằng demo account đã provision, Then chỉ vai trò Curator/Admin đã xác thực được phép và không có thao tác Provider; evidence không diễn giải điều này thành schema/kiến trúc một người dùng vĩnh viễn. | NOT_MEASURED |
| AC-004 | REQ-DOC-001 | MUST | Given nguồn nạp, When validate corpus, Then chỉ chấp nhận 3–5 PDF chính thức có text layer, tổng tối đa 200 trang; scan/OCR, DOCX, HTML, TXT bị từ chối; mỗi nguồn có phê duyệt nêu tên trước ingestion. | NOT_MEASURED |
| AC-005 | REQ-DOC-002 | MUST | Given Curator/Admin, When xử lý một PDF, Then có evidence cho upload, hash, extract, chunk, review thủ công, publish/unpublish và index; extraction không tự publish. | NOT_MEASURED |
| AC-006 | REQ-RET-001 | MUST | Given một câu hỏi hợp lệ, When trả lời, Then output là trích xuất/retrieval-first và evidence xác nhận không có answer Provider/API key/lời gọi mô hình sinh. | NOT_MEASURED |
| AC-007 | REQ-RET-002 | MUST | Given tài liệu/version không `PUBLISHED` hoặc không active, When truy vấn, Then không có chunk hay citation của chúng trong kết quả. | NOT_MEASURED |
| AC-008 | REQ-RET-003 | MUST | Given kết luận thực chất, When xuất đáp án, Then mỗi kết luận có citation backend-derived gồm title/number, Điều/Khoản/Điểm hoặc trang, excerpt và canonical URL. | NOT_MEASURED |
| AC-009 | REQ-RET-004 | MUST | Given 2 ca ngoài corpus, 1 ca mơ hồ và 1 trong 3 ca đa nguồn có evidence mâu thuẫn đáng kể trong bộ 15 ca, When xử lý, Then từng ca trả refusal có cấu trúc và không có answer-model call. | NOT_MEASURED |
| AC-010 | REQ-RET-005 | MUST | Given metadata hiệu lực chưa được curator xác nhận, chỉ dẫn độc hại của người dùng hoặc chỉ dẫn nhúng trong nguồn, When xử lý, Then không suy luận hiệu lực, không thực thi chỉ dẫn và không cho chúng ghi đè scope, publish filter, citation hoặc refusal; chỉ xuất output canonical-cited khi evidence đủ, nếu không refusal có cấu trúc. | NOT_MEASURED |
| AC-011 | REQ-UX-001 | SHOULD | Given màn hình chat demo, When người dùng xem màn hình, Then thấy notice “không phải tư vấn pháp lý”. | NOT_MEASURED |
| AC-012 | REQ-OPS-001 | MUST | Given vận hành demo, When Curator/Admin quản lý corpus, Then môi trường là local/demo cô lập và chỉ có lifecycle corpus; Compose chỉ được chứng minh khi ADR/stack sau này đã duyệt. | NOT_MEASURED |
| AC-013 | REQ-NFR-001 | MUST | Given log/audit demo, When kiểm tra mẫu log và retention cấu hình, Then không có full chat/prompt/context/document; log kỹ thuật redacted tối đa 14 ngày và audit admin tối đa 30 ngày theo mặc định demo. | NOT_MEASURED |
| AC-014 | REQ-NFR-002 | SHOULD | Given máy và workload đã ghi nhận, When chạy 5 phiên chat đồng thời, Then report có P50/P95/P99, success rate và đối chiếu mục tiêu sơ bộ P95 <=30 giây; nếu không chạy ghi `NOT_MEASURED`. | NOT_MEASURED |
| AC-015 | REQ-DATA-001 | MUST | Given frozen demo acceptance fixture, When review manifest, Then có đúng 15 ca: 8 trực tiếp, 3 đa nguồn (1 ca có evidence mâu thuẫn đáng kể và expected refusal), 2 ngoài corpus, 1 mơ hồ, 1 prompt-injection; mọi ca có provenance và expected canonical-cited answer hoặc refusal. Ca prompt-injection không được ghi đè scope, publish filter, citation hoặc refusal; fixture không phải Golden Answer/training dataset và không đi vào Answer Improvement. | NOT_MEASURED |
| AC-016 | REQ-PLN-001 | MUST | Given ngày khởi động được phê duyệt, When review scope, ưu tiên và evidence, Then timebox là đúng 10 ngày dương lịch liên tiếp; việc không hoàn thành/có evidence trong timebox bị loại, để `LATER` hoặc ghi `NOT_MEASURED`, không được trình bày là cam kết giao hàng, production readiness/SLA hoặc hoàn thành prompt tương lai. | NOT_MEASURED |
| AC-017 | REQ-AI-001 | LATER | Given Core Demo, When review scope và roadmap, Then không có feedback/Golden Answer/dataset/evaluation/candidate/fine-tuning trong core; triển khai sau tuân thủ Group 06 và các HR liên quan. | NOT_MEASURED |
| AC-018 | REQ-OPS-002 | LATER | Given Core Demo, When review deliverables, Then không bao gồm các năng lực production, HA/Kubernetes/SSO/live Provider/OCR/extra formats/bulk/multi-domain/mobile/deployment/backup-DR. | NOT_MEASURED |

## Scope-lock gate — Prompt 01.2

Đây là review tài liệu hiện tại, khác với nghiệm thu sản phẩm tương lai.

| AC | Bằng chứng review | Trạng thái |
|---|---|---|
| AC-SL-001 | `docs/scope-v1.md` có in-scope/out-of-scope, persona, user story, corpus, demo data, NFR, 10 ngày và quyết định mở. | Đã soạn; chờ Orchestrator review. |
| AC-SL-002 | Mọi requirement trong catalog có ID `REQ-*` ổn định và đúng một priority; mọi ID được map sang bảng này và RTM. | Đã soạn; chờ validation độc lập. |
| AC-SL-003 | Không có MUST mơ hồ làm đổi boundary/schema; exact corpus/approver, benchmark machine, demo dates/team capacity được ghi rõ là chi tiết thực thi không đổi boundary/schema. | Đã soạn; chờ người dùng duyệt. |
| AC-SL-004 | Người dùng phải duyệt phạm vi trước prompt kế tiếp; Prompt 02.1 mới phê duyệt final boundary/ownership. | Chưa duyệt người dùng. |
| AC-SL-005 | Điều kiện dependency của REQ-RET-003 được ghi rõ: manifest hiện tại xếp 05.8 Citation sau 05.7 → 05.6 → 05.5 Provider, trong khi 05.6 yêu cầu real minimal Provider request; mâu thuẫn với Core không Provider/credential/cost. Citation vẫn là Core MUST và cần quyết định governance/manifest tương lai được phê duyệt riêng trước khi planning downstream khẳng định đường đi khả thi. | Điều kiện còn mở; Prompt 01.2 không sửa manifest/prompt tương lai. |

Scope-lock không xác nhận sản phẩm đã tồn tại hay đạt các AC-001 đến AC-018.
