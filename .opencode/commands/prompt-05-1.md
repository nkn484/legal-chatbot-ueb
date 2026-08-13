---
description: "05.1 - Retrieval contract và query normalization"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 05.1 — Retrieval contract và query normalization

Prompt ID: `05.1`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 05.1`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 05.1`.
3. Chạy `python scripts/prompt_gate.py start 05.1`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `04.13`.

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

**Mục tiêu duy nhất:** Chốt request/response của Retrieval Service.

**Công việc:** Giữ câu gốc; normalize không mất số ký hiệu/Điều/Khoản/Điểm; allowlisted filters; access context; response chứa raw/fused/rerank scores, versions, freshness, sufficiency/reason codes.

**Đầu ra:** Contract implementation skeleton và tests validation.

**Cổng PASS:** Client không ép lấy unpublished/unauthorized; query length/filter cardinality bị giới hạn.

**Cấm:** Gọi LLM sinh câu trả lời.

**Dừng:** Chờ inspect contract.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/05.1.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 05.1 --report docs/progress/05.1.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
