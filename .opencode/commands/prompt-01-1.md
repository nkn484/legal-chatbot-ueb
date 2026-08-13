---
description: "01.1 - Kiểm kê repository"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 01.1 — Kiểm kê repository

Prompt ID: `01.1`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 01.1`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 01.1`.
3. Chạy `python scripts/prompt_gate.py start 01.1`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `Không có`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `oracle`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/`
- `.agent-run/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Lập ảnh chụp trạng thái hiện tại, chưa sửa mã nguồn.

**Đầu vào:** Repository; `README.md`; `00_NGUYEN_TAC_CUNG.md`.

**Công việc:** Kiểm kê source, service, migration, contract, Docker, CI, test, tài liệu, thay đổi chưa commit và secret có nguy cơ bị lộ. Đối chiếu với danh mục nhóm prompt.

**Đầu ra:** `docs/project-state.yaml`, `docs/repository-inventory.md`, `docs/known-limitations.md`.

**Cổng PASS:** Mọi artifact hiện có được phân loại `EXISTS | PARTIAL | MISSING | UNKNOWN`; không sửa business code; không in secret.

**Cấm:** Tạo service, sửa kiến trúc hoặc tự coi file tồn tại là đã đạt.

**Dừng:** Báo cáo theo mẫu HR và chờ duyệt.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/01.1.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 01.1 --report docs/progress/01.1.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
