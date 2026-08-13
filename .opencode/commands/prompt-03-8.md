---
description: "03.8 - Audit append-only"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 03.8 — Audit append-only

Prompt ID: `03.8`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 03.8`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 03.8`.
3. Chạy `python scripts/prompt_gate.py start 03.8`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `03.7`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `fixer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/`
- `packages/`
- `infra/`
- `deploy/`
- `.github/`
- `docs/`
- `tests/`
- `Makefile`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Tạo nhật ký quản trị có thể truy nguyên.

**Công việc:** Audit schema allowlist; actor/action/target/result/time/IDs; before-after redaction; append-only/hash-chain; query có quyền; async command/event intake.

**Đầu ra:** Audit code/migration/tests và integrity check.

**Cổng PASS:** Truy từ admin action tới request; secret canary không xuất hiện; record không sửa tại chỗ.

**Cấm:** Cho service khác ghi trực tiếp audit DB.

**Dừng:** Chờ duyệt.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/03.8.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 03.8 --report docs/progress/03.8.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
