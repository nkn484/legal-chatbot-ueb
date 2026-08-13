---
description: "06.8 - Metrics và slicing"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 06.8 — Metrics và slicing

Prompt ID: `06.8`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 06.8`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 06.8`.
3. Chạy `python scripts/prompt_gate.py start 06.8`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `06.7`.

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

**Mục tiêu duy nhất:** Tính chỉ số đúng và phát hiện regression cục bộ.

**Công việc:** Citation validity/precision/recall; groundedness theo claim; correctness; Recall@K/MRR/nDCG; correct abstention/false refusal; injection resistance; schema success; latency/token/cost; slice theo lĩnh vực/loại/độ khó.

**Đầu ra:** Metric implementations/tests/report template.

**Cổng PASS:** Denominator rõ; thiếu mẫu ghi NOT_MEASURED; không chỉ dùng trung bình tổng; judge version/bias được báo cáo.

**Cấm:** Dùng một LLM judge làm nguồn quyết định duy nhất.

**Dừng:** Chờ duyệt thresholds.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/06.8.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 06.8 --report docs/progress/06.8.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
