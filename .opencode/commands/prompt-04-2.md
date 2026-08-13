---
description: "04.2 - Upload và object storage"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 04.2 — Upload và object storage

Prompt ID: `04.2`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 04.2`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 04.2`.
3. Chạy `python scripts/prompt_gate.py start 04.2`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `04.1`.

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

**Mục tiêu duy nhất:** Nạp file gốc an toàn.

**Công việc:** Streaming/presigned upload; SHA-256; MIME sniffing; size/type allowlist; safe filename; storage key nội bộ; malware-scan hook; duplicate-byte handling.

**Đầu ra:** Upload API/adapter/tests.

**Cổng PASS:** PDF/DOCX/HTML/TXT hợp lệ; extension giả, path traversal, file quá lớn/hỏng bị chặn; API không lộ storage credential/key.

**Cấm:** Đưa file chưa scan vào processing.

**Dừng:** Chờ security review upload.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/04.2.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 04.2 --report docs/progress/04.2.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
