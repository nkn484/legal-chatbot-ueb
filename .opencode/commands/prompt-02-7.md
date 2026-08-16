---
description: "02.7 Revision 2 - Cổng kiến trúc hiệu chỉnh và nghiệm thu lại"
agent: orchestrator
subtask: false
---

# Thực thi Prompt 02.7 Revision 2 — Hiệu chỉnh kiến trúc và nghiệm thu lại

Prompt ID: `02.7`. Chỉ thực hiện prompt này: đối soát và hiệu chỉnh tám blocker kiến trúc Nhóm 2 có bằng chứng, sau đó chạy lại cổng nghiệm thu. Không triển khai business code hoặc runtime implementation; phải dừng sau khi submit.

Vì Prompt 02.7 hiện có trạng thái `FAIL`, người dùng phải chạy `reopen` **ngoài OpenCode** sau khi restart trước khi thực hiện Revision 2. Agent không bao giờ chạy `reopen`.

## Gate context tự động

!`python scripts/prompt_gate.py context 02.7`

Nếu `eligible=false`, không sửa file và trả `BLOCKED`. Nếu đủ điều kiện:

1. Đọc `@AGENTS.md` và `@prompts/00_HARD_RULES.md`.
2. Chạy `python scripts/prompt_gate.py check 02.7`.
3. Chạy `python scripts/prompt_gate.py start 02.7`.
4. Chạy `python scripts/prompt_gate.py status 02.7`, kiểm tra `git status --short` và bảo toàn thay đổi hiện hữu.

Dependency trực tiếp: `02.6`.

## Hợp đồng điều phối OMO-slim

Ưu tiên lane read-only: `oracle`, `librarian`, `council`, `explorer`. Mặc định chỉ một `fixer` là writer; Orchestrator là validation owner.

Trước khi delegate, Orchestrator phải nêu task graph và ownership. Explorer/Librarian/Oracle/Council chỉ đọc. Fixer/Designer chỉ được sửa trong write roots dưới đây; mặc định chỉ một writer:

- `prompts/manifest.json`
- `docs/decision-log.md`
- `docs/architecture/`
- `contracts/`
- `docs/progress/`
- `scripts/prompt_gate.py`
- `scripts/verify_pack.py`
- `tests/test_prompt_gate_lifecycle.py`
- `docs/prompt-transition-rules.md`
- `.opencode/commands/prompt-02-7.md` chỉ khi báo cáo hash của command hiện tại; cấm sửa mọi file `.opencode` khác.

Mỗi subtask phải tự đủ context: objective, constraints, file/search scope, write permission, expected output, validation và điều cấm. Không giao toàn bộ prompt nguyên khối cho specialist.

## Mục tiêu và hiệu chỉnh bắt buộc

**Mục tiêu duy nhất:** Đối soát toàn bộ tám blocker kiến trúc Nhóm 2 có bằng chứng, tạo revision rõ ràng cho artifact bị ảnh hưởng, rồi chạy lại acceptance gate. Không có business code hay runtime implementation trong prompt này.

Thực hiện chính xác các corrective requirement sau:

1. **B-001 / DEC-005:** Citation-service là Core và độc lập Provider. Thêm revision quyết định đã duyệt mới nhất có hiệu lực hoặc closure thay thế; cập nhật manifest/dependency để implementation Citation không bị chặn bởi Provider 05.5–05.7. Provider vẫn là `LATER`. Không bao giờ thêm Provider vào Core hoặc defer Citation.
2. **B-002 / DEC-007:** Triển khai và tài liệu hóa `latest-effective with history`: entry quyết định cũ là bất biến; sửa đổi tạo revision mới đã duyệt với `decision_key`/`revision`/`supersedes`/`effective_at`; revision đã duyệt mới nhất, không bị revoke, trong chuỗi hợp lệ là effective. Thêm closure reference cần human approval tới governance evidence commit/tests, nhưng prompt này chỉ đề xuất candidate chờ human approval. Quyết định governance phải được human-approved: `reopen` hỗ trợ terminal `PASS` và `FAIL` với archived disposition semantics bất biến, riêng biệt; `PASS` archive approval, `FAIL` archive rejection; cả hai tăng revision và trả về `IN_PROGRESS`. Không bao giờ xem `FAIL` là effective approval và cấm transition trực tiếp `FAIL→PASS`. Giữ metadata report/evidence/snapshot cũ trong history; hash thiếu từ legacy phải đánh dấu `NOT_CAPTURED_LEGACY`, không được bịa. Bắt buộc có lifecycle tests và `verify_pack`. Không viết lại hoặc xóa lịch sử DEC-007 cũ.
3. **B-003:** Đối soát `api-gateway -> processing-service` trong sync topology cho `getProcessingJob`; chứng minh DAG vẫn acyclic.
4. **B-004:** Thêm versioned internal Identity HTTP contract với semantics verification/context có giới hạn, scopes/service identity/deadline/sanitized errors, examples và lint inventory. Core vẫn là local/demo identity; live OIDC/JWKS vẫn là `LATER`.
5. **B-005:** Đối soát status/acceptance lineage của ADR-001..005 với revision 02.2 đã được phê duyệt; bảo toàn lịch sử.
6. **B-006:** Cập nhật threat DFD/privacy flow registry cho các delivery và validator có hướng: Document→Processing, Processing→Document, Index→Document, Document→Citation.
7. **B-007:** Tách producer AuditFact Core đang active (`identity`, `document`, `processing`, `index`, `retrieval`, `citation`, `chat`) khỏi producer dự kiến `LATER` (`provider`, `feedback`, `evaluation`); chỉ producer Core active được routable/ACL-enabled; producer planned chỉ metadata-only và denied.
8. **B-008:** Disposition mọi item trong `schema-open-fields.md` thành `RESOLVED` kèm exact contract evidence, hoặc `DEFERRED`/`LATER` kèm owner, approval requirement và không còn stale deadline.

Cập nhật supplemental traceability, baseline và gate tooling sau hiệu chỉnh. Xử lý initial baseline phải bảo toàn baseline trước đó và tạo evidence revision/diff, không được thay thế im lặng.

## Nghiệm thu lại

Chạy schema/OpenAPI/AsyncAPI/security/architecture-gate validators, compatibility checks, cycle/cross-DB checks và snapshot preservation. Chỉ nêu gate candidate khi `blockers=0` và `errors=0`; parser/runtime test chính thức là điều kiện `NOT_MEASURED`.

**PASS gate:** `0` blocker, không có breaking inconsistency hoặc security architecture blocker, mọi open decision key có effective human-approved disposition candidate đang chờ approval; runtime Critical/High vẫn activation-blocked.

**Cấm:** approve/reject/defer; sửa trực tiếp state; thay đổi contract im lặng; business code; Provider Core; Citation defer; mutable overwrite lịch sử decision; chạy prompt tiếp theo.

**Dừng:** Chỉ đề xuất prompt tiếp theo, không chạy prompt đó.

## Đầu ra kiểm soát bắt buộc

Phải tạo `docs/progress/02-architecture-gate.md`, `docs/progress/02.7.md` theo `docs/templates/progress-report.md`, các evidence report thực tế, và artifact approved bị ảnh hưởng thông qua explicit revision. Báo cáo phải ghi lệnh test và kết quả thực tế; không dùng mô tả thay bằng chứng.

Khi hoàn thành, submit bằng một hoặc nhiều `--evidence` là file/test report thực sự:

```bash
python scripts/prompt_gate.py submit 02.7 --report docs/progress/02.7.md --evidence <DUONG_DAN_BANG_CHUNG>
```

Sau khi trạng thái thành `AWAITING_APPROVAL`, dừng hoàn toàn. Không gọi command tiếp theo, không chạy approve/reject/defer và không sửa trực tiếp state.
