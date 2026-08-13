---
description: "07.8 - Reliability, backup và chaos"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 07.8 — Reliability, backup và chaos

Prompt ID: `07.8`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 07.8`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 07.8`.
3. Chạy `python scripts/prompt_gate.py start 07.8`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `07.7`.

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

**Mục tiêu duy nhất:** Xác minh phục hồi và graceful degradation.

**Công việc:** Timeout/retry matrix; circuit breaker; load shedding; outbox/inbox reconciliation; DLQ replay; backup/restore; provider/RabbitMQ/worker/DB/object-store failure; RPO/RTO đo thực tế.

**Đầu ra:** Runbooks, chaos tests, restore report.

**Cổng PASS:** Replay không duplicate side effects; restore thành công; request thất bại an toàn; số liệu không suy đoán.

**Cấm:** Chaos trên production hoặc dữ liệu thật chưa ủy quyền.

**Dừng:** Chờ operations review.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/07.8.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 07.8 --report docs/progress/07.8.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
