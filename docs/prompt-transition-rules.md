# Quy tắc chuyển tiếp prompt

Tài liệu này là diễn giải coordination, không phải máy trạng thái và không có quyền ghi `.agent-run/prompt-state.json`.

## A. Đồ thị runtime thực thi

Nguồn hành vi duy nhất là `scripts/prompt_gate.py`; dependency tĩnh là `prompts/manifest.json`; state mutable duy nhất là `.agent-run/prompt-state.json`.

`start` chỉ chấp nhận prompt eligible ở `NOT_STARTED`, `BLOCKED` hoặc `IN_PROGRESS`; dependency phải là `PASS` hoặc `DEFERRED` và có `human_approved_at` truthy. Nó ghi `IN_PROGRESS` (trừ khi đã `IN_PROGRESS`). `submit` chỉ nhận `IN_PROGRESS`, report/evidence tồn tại trong repository, ít nhất một evidence, và năm marker; sau đó ghi `AWAITING_APPROVAL`. Người dùng `approve` từ `AWAITING_APPROVAL` ghi `PASS`; `reject` ghi `FAIL`. `defer-group` ghi `DEFERRED` chỉ cho toàn bộ item `NOT_STARTED` của group.

Runtime literals là `NOT_STARTED`, `IN_PROGRESS`, `AWAITING_APPROVAL`, `PASS`, `FAIL`, `DEFERRED`. `AWAITING_APPROVAL` và `DEFERRED` phải được tính đến dù mô hình wording cấp cao không nêu chúng.

## B. Mô hình outcome tài liệu được yêu cầu

Mô hình diễn giải cấp cao là `NOT_STARTED -> IN_PROGRESS -> PASS/PASS_WITH_CONDITIONS/FAIL/BLOCKED`. Đây không thay thế runtime: `PASS_WITH_CONDITIONS` và `BLOCKED` là outcome tài liệu, không là normal persisted transition. Candidate report dùng `PASS_CANDIDATE`, `PASS_WITH_CONDITIONS_CANDIDATE`, `BLOCKED`, hoặc `FAIL`.

Qualified pass chỉ map sang runtime `PASS` sau human approval theo thủ tục, với điều kiện được ghi rõ trong approval note và liên kết decision log. `BLOCKED` trong tài liệu không đổi runtime.

## C. Thứ bậc thẩm quyền

1. `scripts/prompt_gate.py`: hành vi executable.
2. `prompts/manifest.json`: ID, dependency và metadata tĩnh.
3. `.agent-run/prompt-state.json`: runtime mutable authoritative duy nhất.
4. `docs/prompt-state.yaml`, tài liệu này và decision log: registry/giải thích không có quyền runtime.

## D. Bảng command và tiền điều kiện

| Command | Tiền điều kiện | Kết quả runtime |
|---|---|---|
| `context` / `check` | eligible theo dependency và current state | chỉ xuất context/eligibility; không ghi |
| `start` | eligible; current `NOT_STARTED`, `BLOCKED`, hoặc `IN_PROGRESS` | `IN_PROGRESS` |
| `submit` | `IN_PROGRESS`, report/evidence in-repo tồn tại, >=1 evidence, 5 marker | `AWAITING_APPROVAL` |
| `approve` | `AWAITING_APPROVAL`, `--by`/`--note` không rỗng | `PASS` |
| `reject` | `AWAITING_APPROVAL`, `--by`/`--note` không rỗng | `FAIL` |
| `defer-group` | group tồn tại, điều kiện dependency của item đầu tiên đạt, mọi item `NOT_STARTED` | `DEFERRED` cho group |

## E. Cổng report/evidence và giới hạn chất lượng

Không có `PASS` nếu chưa có submitted report + nonempty evidence và human approval theo thủ tục. Gate chỉ kiểm tra tồn tại cấu trúc: report/evidence, repository boundary, và marker `Trạng thái`, `Đã thay đổi`, `Bằng chứng`, `Sai lệch`, `Đề xuất prompt tiếp theo`.

Gate không kiểm evidence quality, relevance, hash, binding tới `required_report`, hay test thực sự pass. Documentation không thể bảo đảm quality; Orchestrator/human verification vẫn bắt buộc.

## F. Dependency, human approval và successor lock

Mỗi dependency phải persisted `PASS` hoặc `DEFERRED` **và** `human_approved_at` truthy. Vì vậy submit không mở successor; chỉ approval/defer hợp lệ mới mở. Human approval là procedural/audit metadata, script không xác thực danh tính bằng mật mã.

## G. Ownership và hành động cấm

Orchestrator chịu trách nhiệm coordination, reread, validation độc lập và submit. Agent chỉ có thể chạy `check`/`start`/`submit` khi prompt command yêu cầu. Agent bị cấm `approve`, `reject`, `defer-group`, direct state edit, hoặc quản lý `.agent-run/`; chỉ human thực hiện approval/rejection/deferral. Docs không authorize, transition hay unlock prompt.

## H. Recovery, reject, defer và discrepancy

`FAIL` sau reject không nằm trong tập `start` cho phép; recovery không được script tự định nghĩa. `BLOCKED` được `start` chấp nhận nhưng không có command ghi `BLOCKED`. Không có command persist `PASS_WITH_CONDITIONS`. `defer-group` kiểm dependency của **item đầu tiên** trong group, không kiểm từng item trước khi defer; approval fields cũng được tái sử dụng cho reject/defer. `required_report` trong manifest được context hiển thị nhưng submit không bắt buộc report path trùng field đó. Các sai khác được đăng ký tại DEC-007.

## I. Carry-forward điều kiện 01.2

DEC-005 vẫn OPEN: REQ-RET-003 citation là Core MUST, nhưng manifest xếp `05.8` sau `05.7 -> 05.6 -> 05.5`; 05.6 cần real minimal Provider request, mâu thuẫn Core không Provider/credential/cost. Chỉ governance/manifest resolution tương lai được phê duyệt riêng mới có thể cho phép claim feasible downstream path. Prompt 01.3 không giải quyết điều kiện này.
