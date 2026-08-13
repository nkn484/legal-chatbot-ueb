---
description: "02.5 - AsyncAPI và độ tin cậy event"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.5 — AsyncAPI và độ tin cậy event

Prompt ID: `02.5`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.5`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.5`.
3. Chạy `python scripts/prompt_gate.py start 02.5`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `02.4`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `oracle`, `librarian`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/architecture/`
- `contracts/`
- `docs/progress/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Chốt event contracts và delivery semantics.

**Công việc:** Định nghĩa event envelope và các event document processing/publish/index/provider/chat/feedback/golden/dataset/evaluation/candidate. Ghi producer, consumer, ordering, retention, retry, DLQ và idempotency key.

**Đầu ra:** `contracts/asyncapi/asyncapi.yaml`, schema/examples, event ownership matrix.

**Cổng PASS:** AsyncAPI lint; duplicate/out-of-order scenarios được mô tả; payload không chứa secret/full document text ngoài nhu cầu.

**Cấm:** Cam kết exactly-once xuyên hệ thống; dùng event như shared database.

**Dừng:** Chờ duyệt.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/02.5.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.5 --report docs/progress/02.5.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
