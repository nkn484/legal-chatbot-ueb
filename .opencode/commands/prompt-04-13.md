---
description: "04.13 - Cổng nghiệm thu pipeline dữ liệu"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 04.13 — Cổng nghiệm thu pipeline dữ liệu

Prompt ID: `04.13`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 04.13`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 04.13`.
3. Chạy `python scripts/prompt_gate.py start 04.13`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `04.12`.

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

**Mục tiêu duy nhất:** Kiểm tra vertical slice upload → review → publish → index.

**Công việc:** Chạy file text PDF, scan PDF, DOCX, HTML, TXT; duplicate, corrupt, OCR thấp, replay, unpublish/reindex.

**Đầu ra:** `docs/progress/04-data-pipeline-gate.md`, benchmark CPU/RAM/time/page.

**Cổng PASS:** HR-15 và HR-21 chứng minh bằng test; source/page/chunk/hash truy nguyên đầy đủ; không secret/text nguồn trong log mặc định.

**Cấm:** Dùng fixture giả để che lỗi extractor/OCR thực.

**Dừng:** Chỉ đề xuất Prompt 05.1.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/04.13.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 04.13 --report docs/progress/04.13.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
