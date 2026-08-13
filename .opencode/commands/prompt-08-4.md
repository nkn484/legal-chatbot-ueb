---
description: "08.4 - E2E Answer Improvement"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 08.4 — E2E Answer Improvement

Prompt ID: `08.4`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 08.4`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 08.4`.
3. Chạy `python scripts/prompt_gate.py start 08.4`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `08.3`.

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

**Mục tiêu duy nhất:** Test feedback → review → golden → dataset → evaluation → candidate.

**Công việc:** Poisoning/PII/leakage/invalid citation/revoke; reviewer conflict; freeze; restart eval; good/bad candidate; approval/release separation.

**Đầu ra:** E2E report và lineage manifest.

**Cổng PASS:** Không unapproved data; frozen immutable; bad candidate fail; không auto-release.

**Cấm:** Gọi fine-tuning thật nếu chưa có ủy quyền riêng.

**Dừng:** Chờ duyệt.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/08.4.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 08.4 --report docs/progress/08.4.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
