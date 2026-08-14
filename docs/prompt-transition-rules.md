# Quy tắc chuyển tiếp prompt

Tài liệu này diễn giải runtime executable; không có quyền ghi `.agent-run/prompt-state.json`.

## A. Nguồn thẩm quyền và compatibility

1. `scripts/prompt_gate.py` là máy trạng thái executable.
2. `prompts/manifest.json` cung cấp dependency và `write_roots` tĩnh.
3. `.agent-run/prompt-state.json` là state mutable duy nhất.

State legacy được đọc tương thích: thiếu `revision` nghĩa là `1`; thiếu `history` và `approval_history` nghĩa là danh sách rỗng; thiếu `approved_revision` chỉ có hiệu lực là `1` khi entry legacy là `PASS`/`DEFERRED` và có `human_approved_at`. Đọc không mass-migrate hoặc sửa state; mutation chỉ bổ sung field cho target thích hợp.

## B. Đồ thị runtime và revision-bound approval

`start` từ `NOT_STARTED`/`BLOCKED` chuyển sang `IN_PROGRESS`; resume `IN_PROGRESS` không tạo snapshot legacy. `submit` chuyển `IN_PROGRESS` sang `AWAITING_APPROVAL`; `approve` chuyển sang `PASS`; `reject` sang `FAIL`; `defer-group` chuyển các target hợp lệ sang `DEFERRED`.

Dependency chỉ accepted khi predecessor có status `PASS` hoặc `DEFERRED`, `human_approved_at` truthy, và `approved_revision == revision` theo effective legacy/current value. Vì vậy `submit` không mở successor; `approve` hoặc `defer-group` mới mở. Khi parent được `reopen`, parent là `IN_PROGRESS` revision mới nên direct successor bị derived blocking; successor xa cũng bị block vì predecessor trực tiếp không thể advance. Không persist state `BLOCKED` cho successor.

`approve` và `defer-group` ghi `approved_revision` bằng revision hiện tại, giữ current compatibility fields và append immutable `approval_history` gồm revision, at/by/note và snapshot report/evidence/submitted. `--by` là procedural identity/audit metadata; cryptographic authentication nằm ngoài gate hiện tại.

## C. Snapshot artifact và controlled cancellation

Lần chuyển thực sự đầu tiên từ `NOT_STARTED`/`BLOCKED` sang `IN_PROGRESS`, gate lưu `start_snapshot`: version, `started_at`, và map path repo-relative của regular file tới SHA-256 trong `write_roots`. Snapshot chỉ có hash, không có file contents/secret; bỏ `.git` ở mọi depth, `__pycache__`, `*.pyc`, `.DS_Store`, và không follow symlink. Overlapping root được union/dedupe theo path nên hash mỗi file một lần.

Mọi `write_roots` được validate trước snapshot/Git fallback: phải là relative nonempty path (hoặc `.`), không absolute/traversal/escape/symlink root hay symlink ancestor, và không được declared `.git` path segment. Lexical check Windows-normalize từng segment bằng `rstrip(' .').casefold()`, nên `.git`, `.GIT`, `.git.`, `.git ` và nested variants đều bị từ chối trước filesystem access; whole path `.` vẫn hợp lệ. Root missing chỉ hợp lệ nếu nearest existing ancestor an toàn bên trong repo; nó là empty prefix lúc start và creation sau đó là artifact delta. Symlink xuất hiện dưới root hoặc thay root missing cũng fail closed. Root invalid làm `start`, `cancel-start` và `reopen` từ chối không mutation.

`cancel-start PROMPT_ID --by USER --note NOTE` là **human/governance-only**. Nó chỉ chấp nhận `IN_PROGRESS` chưa submit (`submitted_at=null`, `report=null`, evidence rỗng, không current approval). Gate so snapshot hiện tại với `start_snapshot`; created/modified/deleted file trong root đều block. Snapshot legacy không được backfill khi start/resume: no-snapshot hoặc snapshot v1 files-only không có `roots` không được tin để clean; cancellation chỉ được phép bằng `git status --porcelain=v1 --untracked-files=all -- <write_roots>` sạch, recorded với fallback mode riêng. Git unavailable/error hoặc output đều fail closed.

Cancellation không xóa hoặc rollback filesystem, không giảm revision, và không attribution thay đổi cho một người/prompt. Thay đổi bởi bất kỳ ai trong `write_roots` block cancellation; thay đổi ngoài root không bị gate gán cho prompt và cũng không bị xóa. Thành công append `history` event `CANCEL_START` chứa prior `started_at`, revision và `snapshot_mode`, rồi reset runtime submission/start fields thành `NOT_STARTED`.

## D. Reopen có kiểm soát và descendants

`reopen PROMPT_ID --by USER --note NOTE` là **human/governance-only**, chỉ cho `PASS` có current human approval ở current revision. Gate xây reverse dependency graph và fail closed nếu reference unknown hoặc cycle. Nó kiểm deterministic tất cả direct/indirect descendants: chỉ `NOT_STARTED` pristine (`submitted_at/report=null`, evidence rỗng, không approval) được phép. `IN_PROGRESS` bị từ chối rõ ràng và phải `cancel-start` trước; `AWAITING_APPROVAL`, `PASS`, `DEFERRED`, `FAIL`, `BLOCKED` hay descendant có artifact/approval đều bị từ chối.

Trước transition, current approval được archive append-only trong `approval_history` với approval snapshot và metadata archive. Gate append `REOPENED` history với old/new revision, prior approval và descendant IDs checked; tăng revision, clear submission/current approval, ghi reopen metadata, chuyển target `IN_PROGRESS`, và capture baseline snapshot mới. Không mutate successor thành `BLOCKED`. Sau submit + approve revision mới, `approved_revision` mới khớp và successor lại eligible.

## E. Bảng command và ownership

| Command | Tiền điều kiện chính | Kết quả |
|---|---|---|
| `context` / `check` | dependency current-revision approved; graph hợp lệ | chỉ đọc eligibility |
| `start` | eligible; `NOT_STARTED`/`BLOCKED`/`IN_PROGRESS` | `IN_PROGRESS`; capture snapshot chỉ khi actual transition |
| `submit` | `IN_PROGRESS`, report/evidence in-repo, >=1 evidence, 5 marker | `AWAITING_APPROVAL` |
| `approve` | `AWAITING_APPROVAL`, nonempty metadata | `PASS`, revision-bound approval history |
| `reject` | `AWAITING_APPROVAL`, nonempty metadata | `FAIL` |
| `defer-group` | mỗi dependency current-revision approved; targets `NOT_STARTED` | `DEFERRED`, approval history |
| `cancel-start` | human-only; pristine `IN_PROGRESS`; clean snapshot/fallback | `NOT_STARTED`, no rollback |
| `reopen` | human-only; current approved `PASS`; all descendants pristine | target `IN_PROGRESS` revision +1 |

Agent chỉ chạy `check`/`start`/`submit` khi prompt command yêu cầu. Agent bị cấm direct state edit và tất cả `approve`, `reject`, `defer-group`, `cancel-start`, `reopen`; những governance command này chỉ human thực hiện. Documentation không authorize transition.

## F. Giới hạn gate

Gate kiểm structural report/evidence, không chứng minh quality/relevance/hash/binding hay test success. `PASS_WITH_CONDITIONS` và `BLOCKED` là outcome tài liệu, không normal persisted transition. `FAIL` recovery ngoài `reopen` không tự định nghĩa. `required_report` được context hiển thị nhưng submit không buộc path trùng field đó.
