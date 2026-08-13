---
description: "06.7 - Evaluation Runner"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 06.7 — Evaluation Runner

Prompt ID: `06.7`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 06.7`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 06.7`.
3. Chạy `python scripts/prompt_gate.py start 06.7`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `06.6`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `librarian`, `fixer`, `oracle`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/feedback-service/`
- `services/evaluation-service/`
- `packages/contracts/`
- `datasets/`
- `tests/`
- `docs/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Chạy baseline/candidate có thể resume và tái lập.

**Công việc:** Durable async jobs; snapshot dataset/config/code/prompt/model; concurrency/rate/cost budget; cancel/resume; per-sample artifact restricted; deterministic rules trước LLM judge.

**Đầu ra:** Runner/adapters/job state/tests.

**Cổng PASS:** Restart không chạy trùng/tính sai cost; provider fail không giả kết quả; cùng snapshot tái lập được run manifest.

**Cấm:** Gọi provider tốn phí khi chưa có budget/credential approval.

**Dừng:** Chờ duyệt execution plan.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/06.7.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 06.7 --report docs/progress/06.7.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
