---
description: "01.2 - Khóa phạm vi Core Demo"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 01.2 — Khóa phạm vi Core Demo

Prompt ID: `01.2`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 01.2`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 01.2`.
3. Chạy `python scripts/prompt_gate.py start 01.2`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `01.1`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/`
- `.agent-run/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Chốt in-scope/out-of-scope và tiêu chí nghiệm thu.

**Đầu vào:** Kết quả 01.1; yêu cầu người dùng.

**Công việc:** Viết user stories, non-functional requirements, dữ liệu demo, số người dùng đồng thời, giới hạn 10 ngày và phần Answer Improvement triển khai sau nếu cần. Gắn mã `REQ-*` và mức `MUST | SHOULD | LATER`.

**Đầu ra:** `docs/scope-v1.md`, `docs/acceptance-criteria.md`, `docs/requirements-traceability-matrix.md` bản đầu.

**Cổng PASS:** Không còn yêu cầu MUST mơ hồ làm thay đổi boundary/schema; người dùng duyệt phạm vi.

**Cấm:** Hứa production HA/Kubernetes/SSO nếu chưa nằm trong phạm vi.

**Dừng:** Liệt kê quyết định còn mở và chờ duyệt.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/01.2.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 01.2 --report docs/progress/01.2.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
