---
description: "04.9 - Quality gate và review artifact"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 04.9 — Quality gate và review artifact

Prompt ID: `04.9`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 04.9`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 04.9`.
3. Chạy `python scripts/prompt_gate.py start 04.9`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `04.8`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `librarian`, `fixer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/document-service/`
- `services/processing-service/`
- `services/index-service/`
- `packages/contracts/`
- `infra/`
- `tests/`
- `docs/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Quyết định artifact đủ điều kiện kiểm duyệt hay cần xử lý lại.

**Công việc:** Metrics coverage/confidence/structure/empty/duplicate/injection-risk; report theo trang/chunk; `SUCCEEDED | NEEDS_REVIEW | FAILED`; event completed/failed.

**Đầu ra:** Quality rules/version, report API, tests.

**Cổng PASS:** Ngưỡng cấu hình/versioned; không report PASS khi thiếu page; event không chứa full content/secret.

**Cấm:** Quality service tự publish.

**Dừng:** Chờ duyệt ngưỡng.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/04.9.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 04.9 --report docs/progress/04.9.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
