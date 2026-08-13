---
description: "03.3 - Hạ tầng Docker Compose"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 03.3 — Hạ tầng Docker Compose

Prompt ID: `03.3`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 03.3`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 03.3`.
3. Chạy `python scripts/prompt_gate.py start 03.3`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `03.2`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `fixer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/`
- `packages/`
- `infra/`
- `deploy/`
- `.github/`
- `docs/`
- `tests/`
- `Makefile`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Dựng dependency local theo profiles.

**Công việc:** PostgreSQL ownership, RabbitMQ/DLQ, Redis, MinIO; networks tách lớp; volume; healthcheck; resource limits; non-root containers.

**Đầu ra:** `core`, `observability`, `training` profiles; `.env.example` placeholder.

**Cổng PASS:** `docker compose config` hợp lệ; data services không expose host mặc định; không có secret thật.

**Cấm:** Mount Docker socket; dùng chung một DB user toàn quyền.

**Dừng:** Báo dependency chưa chạy nếu môi trường thiếu.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/03.3.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 03.3 --report docs/progress/03.3.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
