---
description: "01.3 - Thiết lập bộ điều phối"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 01.3 — Thiết lập bộ điều phối

Prompt ID: `01.3`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 01.3`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 01.3`.
3. Chạy `python scripts/prompt_gate.py start 01.3`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `01.2`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/`
- `.agent-run/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Tạo cơ chế chạy tuần tự từng prompt.

**Đầu vào:** Phạm vi 01.2 đã duyệt.

**Công việc:** Tạo `docs/prompt-state.yaml`, `docs/progress/`, decision log và quy tắc chuyển trạng thái. Mỗi prompt có dependencies, owner, evidence và gate.

**Đầu ra:** State machine `NOT_STARTED → IN_PROGRESS → PASS/PASS_WITH_CONDITIONS/FAIL/BLOCKED`; template progress report.

**Cổng PASS:** Không thể đánh dấu PASS nếu thiếu evidence; prompt sau bị khóa khi dependency chưa PASS hoặc chưa có human approval.

**Cấm:** Tự chạy bất kỳ prompt nhóm 2 trở đi.

**Dừng:** Chỉ đề xuất Prompt 02.1.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/01.3.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 01.3 --report docs/progress/01.3.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
