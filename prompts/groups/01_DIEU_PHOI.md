# Nhóm 1 — Điều phối và khóa phạm vi

## Prompt 01.1 — Kiểm kê repository

**Mục tiêu duy nhất:** Lập ảnh chụp trạng thái hiện tại, chưa sửa mã nguồn.

**Đầu vào:** Repository; `README.md`; `00_NGUYEN_TAC_CUNG.md`.

**Công việc:** Kiểm kê source, service, migration, contract, Docker, CI, test, tài liệu, thay đổi chưa commit và secret có nguy cơ bị lộ. Đối chiếu với danh mục nhóm prompt.

**Đầu ra:** `docs/project-state.yaml`, `docs/repository-inventory.md`, `docs/known-limitations.md`.

**Cổng PASS:** Mọi artifact hiện có được phân loại `EXISTS | PARTIAL | MISSING | UNKNOWN`; không sửa business code; không in secret.

**Cấm:** Tạo service, sửa kiến trúc hoặc tự coi file tồn tại là đã đạt.

**Dừng:** Báo cáo theo mẫu HR và chờ duyệt.

---

## Prompt 01.2 — Khóa phạm vi Core Demo

**Mục tiêu duy nhất:** Chốt in-scope/out-of-scope và tiêu chí nghiệm thu.

**Đầu vào:** Kết quả 01.1; yêu cầu người dùng.

**Công việc:** Viết user stories, non-functional requirements, dữ liệu demo, số người dùng đồng thời, giới hạn 10 ngày và phần Answer Improvement triển khai sau nếu cần. Gắn mã `REQ-*` và mức `MUST | SHOULD | LATER`.

**Đầu ra:** `docs/scope-v1.md`, `docs/acceptance-criteria.md`, `docs/requirements-traceability-matrix.md` bản đầu.

**Cổng PASS:** Không còn yêu cầu MUST mơ hồ làm thay đổi boundary/schema; người dùng duyệt phạm vi.

**Cấm:** Hứa production HA/Kubernetes/SSO nếu chưa nằm trong phạm vi.

**Dừng:** Liệt kê quyết định còn mở và chờ duyệt.

---

## Prompt 01.3 — Thiết lập bộ điều phối

**Mục tiêu duy nhất:** Tạo cơ chế chạy tuần tự từng prompt.

**Đầu vào:** Phạm vi 01.2 đã duyệt.

**Công việc:** Tạo `docs/prompt-state.yaml`, `docs/progress/`, decision log và quy tắc chuyển trạng thái. Mỗi prompt có dependencies, owner, evidence và gate.

**Đầu ra:** State machine `NOT_STARTED → IN_PROGRESS → PASS/PASS_WITH_CONDITIONS/FAIL/BLOCKED`; template progress report.

**Cổng PASS:** Không thể đánh dấu PASS nếu thiếu evidence; prompt sau bị khóa khi dependency chưa PASS hoặc chưa có human approval.

**Cấm:** Tự chạy bất kỳ prompt nhóm 2 trở đi.

**Dừng:** Chỉ đề xuất Prompt 02.1.

