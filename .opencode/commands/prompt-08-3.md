---
description: "08.3 - E2E hỏi đáp và Provider failures"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 08.3 — E2E hỏi đáp và Provider failures

Prompt ID: `08.3`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 08.3`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 08.3`.
3. Chạy `python scripts/prompt_gate.py start 08.3`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `08.2`.

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

**Mục tiêu duy nhất:** Test chuỗi Chat end-to-end và lỗi Provider.

**Công việc:** Một nguồn, nhiều nguồn, mâu thuẫn, thiếu căn cứ, fake citation, injection, unpublish race; Provider 401/403/404/429/5xx/timeout/invalid schema; activate/rollback race.

**Đầu ra:** E2E report và traces đã redaction.

**Cổng PASS:** Conclusion có canonical citation hoặc refusal; chỉ một ACTIVE; secret không lộ; graceful degradation.

**Cấm:** Mock toàn bộ Citation/Retrieval trong E2E này.

**Dừng:** Chờ duyệt.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/08.3.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 08.3 --report docs/progress/08.3.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
