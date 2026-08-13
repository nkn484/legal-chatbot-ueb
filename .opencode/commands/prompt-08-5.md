---
description: "08.5 - Bộ nghiệm thu AI"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 08.5 — Bộ nghiệm thu AI

Prompt ID: `08.5`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 08.5`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 08.5`.
3. Chạy `python scripts/prompt_gate.py start 08.5`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `08.4`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `fixer`, `oracle`, `council`, `observer`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `tests/`
- `deploy/`
- `docs/`
- `.github/`
- `release/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Xây và khóa test set 50–100 câu có nguồn hợp lệ.

**Công việc:** 60% rõ căn cứ, 20% đa văn bản, 10% thiếu dữ liệu, 10% nhiễu/injection; slice theo loại/cơ quan/điều khoản/tổng hợp/phạm vi/hard negative; human review; test set không tuning.

**Đầu ra:** Frozen acceptance dataset, rubric, provenance, hash.

**Cổng PASS:** Không leakage; citation gold kiểm tra; quyền sử dụng nguồn rõ; coverage đúng tỷ lệ hoặc sai lệch được duyệt.

**Cấm:** Tạo câu/đáp án giả rồi ghi là dữ liệu thực.

**Dừng:** Người dùng inspect từng nhóm câu hỏi.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/08.5.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 08.5 --report docs/progress/08.5.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
