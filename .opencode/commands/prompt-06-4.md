---
description: "06.4 - Golden Answer approval"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 06.4 — Golden Answer approval

Prompt ID: `06.4`. Chỉ thực hiện prompt này và phải dừng sau khi submit.

## Gate context tự động

!`python scripts/prompt_gate.py context 06.4`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 06.4`.
3. Chạy `python scripts/prompt_gate.py start 06.4`.
4. Kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `06.3`.

## Hợp đồng điều phối OMO-slim

Agent phù hợp: `explorer`, `librarian`, `fixer`, `oracle`, `council`.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `services/feedback-service/`
- `services/evaluation-service/`
- `packages/contracts/`
- `datasets/`
- `tests/`
- `docs/`

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Đặc tả công việc

**Mục tiêu duy nhất:** Tạo đáp án chuẩn có citation và phê duyệt.

**Công việc:** Draft/review/approve/revoke; maker-checker; claim-to-chunk mapping; expected refusal/confidence/actions; Citation Service revalidation; immutable versions.

**Đầu ra:** Golden Answer domain/API/migration/tests.

**Cổng PASS:** Không citation/invalid citation không approve; approved record không sửa tại chỗ; revoke phát event/tombstone.

**Cấm:** Copy nguyên answer model thành golden mà không review.

**Dừng:** Chờ inspect examples.

## Đầu ra kiểm soát bắt buộc

Ngoài đầu ra nêu trên, phải tạo `docs/progress/06.4.md` theo `docs/templates/progress-report.md`. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 06.4 --report docs/progress/06.4.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
