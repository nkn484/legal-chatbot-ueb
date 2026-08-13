---
description: "04.1 - Document schema và migration"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 04.1 — Document schema và migration

Prompt ID: `04.1`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 04.1`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 04.1`.
3. Chạy `python scripts/prompt_gate.py start 04.1`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `03.9`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `librarian`, `fixer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/document-service/`
- `services/processing-service/`
- `services/index-service/`
- `packages/contracts/`
- `infra/`
- `tests/`
- `docs/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Tạo mô hình dữ liệu vòng đời văn bản.

**Công việc:** Thiết kế `documents`, immutable `document_versions`, metadata pháp lý, source, file manifest, optimistic version và trạng thái. Tạo migration forward/rollback hoặc forward-fix.

**Đầu ra:** ORM/domain model, migration, state table, tests constraints.

**Cổng PASS:** Không ghi đè version; số ký hiệu trùng chỉ cảnh báo; metadata hiệu lực có provenance/người xác nhận.

**Cấm:** OCR, embedding hoặc search trong Document Service.

**Dừng:** Chờ inspect schema.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/04.1.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 04.1 --report docs/progress/04.1.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
