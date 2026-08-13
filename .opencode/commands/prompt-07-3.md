---
description: "07.3 - Citation viewer và feedback UI"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 07.3 — Citation viewer và feedback UI

Prompt ID: `07.3`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 07.3`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 07.3`.
3. Chạy `python scripts/prompt_gate.py start 07.3`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `07.2`.

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

**Mục tiêu duy nhất:** Cho người dùng kiểm tra nguồn và phản hồi.

**Công việc:** Citation cards title/number/issuer/provision/page/excerpt; open canonical source; sanitize URL/Markdown; useful/not useful/reason; duplicate prevention.

**Đầu ra:** Components/tests XSS/canonical-link/feedback.

**Cổng PASS:** Link/chunk/page đúng backend; model-created URL không render; malicious excerpt/filename vô hiệu hóa.

**Cấm:** Gửi toàn bộ tài liệu sang frontend nếu không cần.

**Dừng:** Chờ inspect.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/07.3.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 07.3 --report docs/progress/07.3.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
