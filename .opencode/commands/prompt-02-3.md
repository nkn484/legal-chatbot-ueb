---
description: "02.3 - Domain schema và state machine"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.3 — Domain schema và state machine

Prompt ID: `02.3`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.3`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.3`.
3. Chạy `python scripts/prompt_gate.py start 02.3`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `02.2`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `oracle`, `librarian`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `docs/architecture/`
- `contracts/`
- `docs/progress/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Định nghĩa schema trung lập công nghệ cho dữ liệu trao đổi.

**Công việc:** Chuẩn hóa Document/Version/Status/Job/Chunk/Index/Retrieval/Chat/GroundedAnswer/Citation/ProviderConfigView/Feedback/GoldenAnswer/Dataset/Evaluation/Candidate. Định nghĩa state transition và invariant.

**Đầu ra:** `contracts/schemas/*.json`, examples success/error/refusal.

**Cổng PASS:** Schema validate; `ProviderConfigView` không có secret; `GroundedAnswer` chỉ nhận chunk IDs, không nhận URL do LLM tạo.

**Cấm:** Gắn schema dùng chung trực tiếp với ORM model nội bộ.

**Dừng:** Xuất danh sách trường còn cần nghiệp vụ xác nhận.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/02.3.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.3 --report docs/progress/02.3.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
