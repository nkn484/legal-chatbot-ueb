# Các agent của Oh-my-opencode-slim và cách dùng trong repository

## Agent lõi

| Agent | Loại | Chức năng | Dùng trong dự án | Không giao |
|---|---|---|---|---|
| Orchestrator | Primary, protected | Lập dependency graph, giao subtask, theo dõi ownership, hợp nhất và verify | Nhận mọi `/prompt-*`, kiểm tra gate và điều phối | Không mặc định viết business code; không tự chuyển prompt |
| Explorer | Subagent, read-only | Tìm file, pattern, dependency và luồng code nhanh | Inventory, impact analysis, tìm implementation hiện hữu | Không sửa file, không quyết định kiến trúc cuối |
| Librarian | Subagent, read-only | Tra tài liệu chính thức và hành vi phụ thuộc phiên bản | FastAPI, PostgreSQL, RabbitMQ, pgvector, OCR, OpenAI-compatible API | Không dùng blog không kiểm chứng làm căn cứ kỹ thuật chính; không sửa repo |
| Oracle | Subagent, read-only | Kiến trúc, trade-off, debug strategy, security/code review | ADR, boundary, threat model, review thay đổi rủi ro cao | Không nhận triển khai thường lệ |
| Council | Agent đa mô hình | Chạy nhiều councillor độc lập rồi tổng hợp | Quyết định khó đảo ngược hoặc có bất đồng lớn | Không dùng cho task đơn giản; không thay người dùng phê duyệt |
| Fixer | Subagent, write-capable | Triển khai task nhỏ, rõ phạm vi, có validation | Backend, migration, infra, test trong `write_scope` | Không tự mở rộng scope hoặc sửa UI khi chưa được giao |
| Designer | Subagent, write-capable | UI/UX, responsive, hierarchy, interaction và visual polish | `apps/web-chat/`, `apps/admin-portal/` | Không sửa backend, database hoặc contract |

## Agent tùy chọn

| Agent | Trạng thái | Chức năng |
|---|---|---|
| Observer | Thường bị tắt nếu preset không cấu hình model đa phương thức | Phân tích hình ảnh, PDF, screenshot và diagram; không phải agent triển khai |

Council gồm nhiều `councillor-*` read-only. Chúng đưa ra các góc nhìn độc lập; Council tổng hợp, còn Orchestrator vẫn chịu trách nhiệm quyết định luồng công việc và verification.

## Ánh xạ gần đúng với đội phát triển

- Orchestrator ≈ Delivery Lead/PO điều phối kỹ thuật.
- Oracle ≈ Solution Architect/Tech Lead reviewer.
- Explorer ≈ Codebase analyst.
- Librarian ≈ Technical researcher.
- Fixer ≈ Backend/Platform developer.
- Designer ≈ Product/UI engineer.
- Council ≈ Architecture review board.
- Observer ≈ Visual analyst.

Đây là ánh xạ trách nhiệm, không phải chức danh cứng. Một agent không được nhận quyền ngoài lane chỉ vì tên vai trò tương tự.

## Tài liệu đối chiếu

- Oh-my-opencode-slim README: https://github.com/alvinunreal/oh-my-opencode-slim
- Background orchestration: https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/background-orchestration.md
- Project-local customization: https://github.com/alvinunreal/oh-my-opencode-slim/blob/master/docs/project-local-customization.md
- OpenCode commands: https://opencode.ai/docs/commands/
- OpenCode rules và AGENTS.md: https://opencode.ai/docs/rules/
- OpenCode permissions: https://opencode.ai/docs/permissions/
