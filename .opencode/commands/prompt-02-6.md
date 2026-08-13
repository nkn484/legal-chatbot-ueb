---
description: "02.6 - Threat model và privacy model"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.6 — Threat model và privacy model

Prompt ID: `02.6`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.6`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.6`.
3. Chạy `python scripts/prompt_gate.py start 02.6`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `02.5`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `oracle`, `librarian`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/architecture/`
- `contracts/`
- `docs/progress/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Nhận diện luồng tin cậy và rủi ro trước triển khai.

**Công việc:** STRIDE + OWASP LLM cho upload, auth, Provider SSRF, prompt injection, insecure output, data poisoning, PII, supply chain, admin actions. Phân loại dữ liệu và retention.

**Đầu ra:** `docs/architecture/threat-model.md`, data-flow diagram, risk register với owner/mitigation/test.

**Cổng PASS:** Mỗi rủi ro Critical/High có biện pháp và test ID; secret/PII flow được chỉ ra.

**Cấm:** Ghi chung chung “dùng mã hóa” mà không chỉ vị trí, khóa và trách nhiệm.

**Dừng:** Chờ duyệt risk acceptance.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/02.6.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.6 --report docs/progress/02.6.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
