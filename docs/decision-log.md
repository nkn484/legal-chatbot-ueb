# Decision log

## Quy cách append-only

Không sửa hoặc xóa entry đã ghi. Mỗi entry mới có: `ID`, `date`, `prompt`, `decision-or-condition`, `basis`, `authority`, `status`, `owner`, `closure evidence`, `supersedes`. Chỉ entry mới được phép supersede entry cũ; `OPEN` không được tự đóng.

## Entries

### DEC-001
- date: 2026-08-13
- prompt: 01.3
- decision-or-condition: Tách authority giữa executable runtime, manifest, state và documentation registry.
- basis: `scripts/prompt_gate.py`, `prompts/manifest.json`, `.agent-run/prompt-state.json`.
- authority: executable/runtime sources.
- status: ACCEPTED
- owner: orchestrator
- closure evidence: `docs/prompt-state.yaml`; `docs/prompt-transition-rules.md`.
- supersedes: none

### DEC-002
- date: 2026-08-13
- prompt: 01.3
- decision-or-condition: Qualified pass dùng `PASS_WITH_CONDITIONS_CANDIDATE` trong report; chỉ procedural human approval với điều kiện rõ trong approval note và liên kết decision log mới map runtime `PASS`.
- basis: runtime không persist PASS_WITH_CONDITIONS; README approval guidance.
- authority: human governance plus executable runtime.
- status: ACCEPTED
- owner: orchestrator
- closure evidence: transition rules section B.
- supersedes: none

### DEC-003
- date: 2026-08-13
- prompt: 01.3
- decision-or-condition: `BLOCKED` là representation tài liệu, không là runtime transition.
- basis: start có thể nhận BLOCKED nhưng không command nào ghi BLOCKED.
- authority: executable runtime.
- status: ACCEPTED
- owner: orchestrator
- closure evidence: transition rules sections A/B/H.
- supersedes: none

### DEC-004
- date: 2026-08-13
- prompt: 01.3
- decision-or-condition: Submit evidence gate là structural, không chứng minh quality/relevance/hash/binding/test success.
- basis: `command_submit` chỉ kiểm path, evidence count và marker.
- authority: executable runtime; human governance for quality.
- status: ACCEPTED
- owner: orchestrator
- closure evidence: transition rules section E.
- supersedes: none

### DEC-005
- date: 2026-08-13
- prompt: 01.2 carried to 01.3
- decision-or-condition: REQ-RET-003 citation MUST conflict remains: `05.8 -> 05.7 -> 05.6 -> 05.5`, while 05.6 requires real minimal Provider request and Core excludes Provider/credential/cost.
- basis: approved 01.2 scope/AC/RTM and current manifest.
- authority: future separately approved governance/manifest resolution.
- status: OPEN
- owner: orchestrator
- closure evidence: Required before any feasible downstream path is claimed; none exists.
- supersedes: none

### DEC-006
- date: 2026-08-13
- prompt: 01.3
- decision-or-condition: Reuse `docs/templates/progress-report.md` unchanged; it supplies all six report sections. Gate itself checks only five markers.
- basis: template and `command_submit` marker list.
- authority: documentation governance/executable runtime.
- status: ACCEPTED
- owner: orchestrator
- closure evidence: template remains unchanged; transition rules section E.
- supersedes: none

### DEC-007
- date: 2026-08-13
- prompt: 01.3
- decision-or-condition: Runtime discrepancy register: no persisted PWC; no command writes BLOCKED; group deferral examines first-item dependency; reject/defer reuse approval fields; required_report is not enforced by submit.
- basis: `scripts/prompt_gate.py`.
- authority: executable runtime.
- status: OPEN/KNOWN
- owner: orchestrator
- closure evidence: Future script/governance change only; none requested in 01.3.
- supersedes: none
