---
description: "02.2 - ADR công nghệ và giao tiếp"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.2 — ADR công nghệ và giao tiếp

Prompt ID: `02.2`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.2`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.2`.
3. Chạy `python scripts/prompt_gate.py start 02.2`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `02.1`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `oracle`, `librarian`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/architecture/`
- `contracts/`
- `docs/progress/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Ghi quyết định kiến trúc, chưa viết business code.

**Công việc:** ADR cho REST + RabbitMQ; PostgreSQL; pgvector thuộc Index; MinIO/S3; Redis chỉ cache/rate limit/lock; monorepo/deploy độc lập; FastAPI async; Next.js; OpenTelemetry/Prometheus; OAuth2/OIDC-ready.

**Đầu ra:** Mỗi ADR có context, options, decision, consequences, reconsideration trigger.

**Cổng PASS:** Mọi lựa chọn có trade-off và phương án bị loại; không coi công nghệ là yêu cầu nghiệp vụ.

**Cấm:** Đưa Kafka/Kubernetes/HA vào MUST nếu phạm vi chưa yêu cầu.

**Dừng:** Chờ người dùng duyệt ADR.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/02.2.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.2 --report docs/progress/02.2.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
