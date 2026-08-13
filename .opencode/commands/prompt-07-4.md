---
description: "07.4 - Admin tài liệu và Provider"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 07.4 — Admin tài liệu và Provider

Prompt ID: `07.4`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 07.4`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 07.4`.
3. Chạy `python scripts/prompt_gate.py start 07.4`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `07.3`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `designer`, `fixer`, `oracle`, `observer`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `apps/web-chat/`
- `apps/admin-portal/`
- `infra/`
- `deploy/`
- `tests/`
- `docs/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Xây màn hình quản trị nội dung và cấu hình model.

**Công việc:** Upload/version/progress/chunk/quality/review/publish/reject/reprocess; Provider draft/validate/activate/rollback; RBAC; confirmation/audit status.

**Đầu ra:** Admin pages/E2E role tests.

**Cổng PASS:** API key write-only, không ở response/DOM/log/client persistence; role thiếu quyền không thao tác; destructive action có confirmation.

**Cấm:** Hiển thị storage key, stack trace hoặc secret rút gọn có thể suy đoán quá mức.

**Dừng:** Chờ admin review.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/07.4.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 07.4 --report docs/progress/07.4.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
