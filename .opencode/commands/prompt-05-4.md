---
description: "05.4 - Evidence sufficiency"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 05.4 — Evidence sufficiency

Prompt ID: `05.4`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 05.4`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 05.4`.
3. Chạy `python scripts/prompt_gate.py start 05.4`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `05.3`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `librarian`, `fixer`, `oracle`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/retrieval-service/`
- `services/provider-service/`
- `services/citation-service/`
- `services/chat-service/`
- `packages/contracts/`
- `tests/`
- `docs/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Xác định khi nào đủ căn cứ để trả lời.

**Công việc:** Rules cho exact identifier, score/margin, coverage, independent sources, conflicting scope/validity, access-filtered; reason codes `NO_MATCH`, `LOW_SCORE`, `INSUFFICIENT_COVERAGE`, `CONFLICTING_SOURCES`, `ACCESS_FILTERED`.

**Đầu ra:** Policy/version/config, tests và threshold-tuning report.

**Cổng PASS:** Query ngoài kho/mơ hồ/mâu thuẫn trả insufficient đúng; không đủ căn cứ không kích hoạt answer model.

**Cấm:** Dùng confidence tự khai của LLM.

**Dừng:** Chờ người dùng duyệt threshold.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/05.4.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 05.4 --report docs/progress/05.4.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
