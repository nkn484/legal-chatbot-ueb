# Chatbot Pháp luật — repository execution contract

Khi nhận `/prompt-*`, đọc AGENTS.md, hard rules và gate context. Chỉ điều phối Prompt ID hiện tại. Không tự chuyển prompt dù mọi test đã đạt.

Trước khi delegate, lập task graph ngắn và khai báo cho từng subtask: agent, objective, read_scope, write_scope, dependency, output, validation và điều cấm. Cho phép read-only lanes chạy song song. Mặc định chỉ một writer hoạt động; writer thứ hai chỉ được phép khi hai write_scope hoàn toàn không giao nhau và không đụng contract, migration hoặc shared package.

Dùng Explorer để khảo sát repo; Librarian cho tài liệu chính thức; Oracle cho quyết định/review rủi ro cao; Council chỉ cho trade-off khó đảo ngược; Fixer cho backend/infra/test; Designer cho UI; Observer cho hình ảnh/PDF nếu đã bật. Specialist output là bằng chứng đầu vào, không phải sự thật cuối cùng. Orchestrator phải verify final state trước khi submit.

Orchestrator và mọi subagent bị cấm chạy approve/reject/defer, sửa trực tiếp state hoặc tự bypass gate. Kết thúc ở AWAITING_APPROVAL và chờ người dùng.
