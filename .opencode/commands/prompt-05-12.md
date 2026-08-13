---
description: "05.12 - Cổng nghiệm thu RAG/Chat"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 05.12 — Cổng nghiệm thu RAG/Chat

Prompt ID: `05.12`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 05.12`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 05.12`.
3. Chạy `python scripts/prompt_gate.py start 05.12`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `05.11`.

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

**Mục tiêu duy nhất:** Kiểm tra Retrieval → Provider → Citation → Answer.

**Công việc:** Test một nguồn, nhiều nguồn, mâu thuẫn, ngoài kho, prompt injection, fake citation, unpublish race, Provider failures, 20–30 concurrent demo sessions.

**Đầu ra:** `docs/progress/05-rag-chat-gate.md`.

**Cổng PASS:** 100% conclusion có canonical citation hoặc refusal; HR-15–18/23/25/26 có test; P95 được đo, không suy đoán.

**Cấm:** Giảm ngưỡng để biến test fail thành PASS.

**Dừng:** Chỉ đề xuất Prompt 06.1.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/05.12.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 05.12 --report docs/progress/05.12.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
