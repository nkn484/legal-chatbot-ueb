---
description: "02.7 - Cổng nghiệm thu kiến trúc"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.7 — Cổng nghiệm thu kiến trúc

Prompt ID: `02.7`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.7`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.7`.
3. Chạy `python scripts/prompt_gate.py start 02.7`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `02.6`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `oracle`, `librarian`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/architecture/`
- `contracts/`
- `docs/progress/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Kiểm tra tính nhất quán của toàn bộ artifact nhóm 2.

**Công việc:** Chạy schema/OpenAPI/AsyncAPI lint, compatibility tests; kiểm tra traceability từ REQ tới service/API/event/test; phát hiện dependency cycle và cross-DB.

**Đầu ra:** `docs/progress/02-architecture-gate.md`.

**Cổng PASS:** Không còn breaking inconsistency hoặc blocker security; mọi quyết định mở được người dùng xử lý.

**Cấm:** Sửa contract ngầm trong lúc chạy gate.

**Dừng:** Chỉ đề xuất Prompt 03.1.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/02.7.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.7 --report docs/progress/02.7.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
