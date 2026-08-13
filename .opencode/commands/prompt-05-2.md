---
description: "05.2 - Hybrid fusion"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 05.2 — Hybrid fusion

Prompt ID: `05.2`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 05.2`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 05.2`.
3. Chạy `python scripts/prompt_gate.py start 05.2`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `05.1`.

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

**Mục tiêu duy nhất:** Hợp nhất keyword và vector results một cách tái lập.

**Công việc:** Lấy top-N hai nhánh; deduplicate chunk/content hash; Reciprocal Rank Fusion; source diversity; context budget; lưu strategy/config/index version.

**Đầu ra:** Fusion engine, config schema, unit/evaluation fixtures.

**Cổng PASS:** Cùng input/version cho cùng ordering; unpublished/unauthorized bị loại; exact identifier không bị semantic result lấn át vô lý.

**Cấm:** Chỉ dùng một cosine threshold làm toàn bộ chính sách.

**Dừng:** Chờ benchmark Recall@K/MRR/nDCG.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/05.2.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 05.2 --report docs/progress/05.2.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
