---
description: "02.1 - Chốt bounded contexts và ownership"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.1 — Chốt bounded contexts và ownership

Prompt ID: `02.1`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.1`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.1`.
3. Chạy `python scripts/prompt_gate.py start 02.1`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `01.3`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `oracle`, `librarian`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/architecture/`
- `contracts/`
- `docs/progress/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Chốt ranh giới service và quyền sở hữu dữ liệu.

**Đầu vào:** Phạm vi đã duyệt; inventory.

**Công việc:** Mô tả API Gateway, Identity/Audit, Document, Processing, Index, Retrieval, Provider, Citation, Chat, Feedback/Annotation, Training/Evaluation. Nêu dữ liệu sở hữu, API/event cung cấp và dependency được phép.

**Đầu ra:** `docs/architecture/container-map.md`, `docs/architecture/data-ownership.md`.

**Cổng PASS:** Không cross-service DB; không vòng phụ thuộc đồng bộ; mỗi năng lực có đúng một owner.

**Cấm:** Tạo service theo từng bảng; shared business-model package.

**Dừng:** Chờ duyệt boundaries.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/02.1.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.1 --report docs/progress/02.1.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
