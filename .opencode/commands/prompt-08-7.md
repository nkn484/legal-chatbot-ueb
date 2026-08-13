---
description: "08.7 - Release package và runbooks"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 08.7 — Release package và runbooks

Prompt ID: `08.7`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 08.7`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 08.7`.
3. Chạy `python scripts/prompt_gate.py start 08.7`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `08.6`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `fixer`, `oracle`, `council`, `observer`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `tests/`
- `deploy/`
- `docs/`
- `.github/`
- `release/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Đóng gói bản demo có thể triển khai và vận hành.

**Công việc:** Compose profiles/env placeholders; migrations/seeds; pinned contracts/images; startup/shutdown; backup/restore; rotate secret; Provider rollback; DLQ replay; reprocess/reindex; incident response; architecture/ADR/limitations/SBOM/test reports/demo script.

**Đầu ra:** Versioned release artifact và checksums.

**Cổng PASS:** Cài mới từ hướng dẫn trên môi trường sạch; không secret; rollback/runbook đã test.

**Cấm:** Triển khai production hoặc dùng credential thật ngoài ủy quyền.

**Dừng:** Chờ bàn giao review.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/08.7.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 08.7 --report docs/progress/08.7.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
