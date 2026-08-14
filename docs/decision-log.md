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

### DEC-008
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: `cancel-start` là controlled reset chỉ cho IN_PROGRESS pristine, có metadata human và evidence artifact clean.
- basis: user-approved gate governance checkpoint.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section C.
- supersedes: recovery undefined wording in DEC-007 only for controlled cancellation.

### DEC-009
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: `reopen` tạo revision mới, archive approval append-only, và chỉ cho khi toàn bộ descendants pristine NOT_STARTED; IN_PROGRESS phải cancel-start trước.
- basis: user-approved gate governance checkpoint.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section D.
- supersedes: none

### DEC-010
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: Start snapshot hash detects artifacts under write_roots; legacy cancellation uses fail-closed clean Git fallback; cancellation never deletes/restores files.
- basis: user-approved gate governance checkpoint.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section C.
- supersedes: none

### DEC-011
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: Human approval is bound to current revision; reopening derives successor blocking until new revision submit and approval complete.
- basis: user-approved gate governance checkpoint.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section B/D.
- supersedes: none

### DEC-012
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: Artifact root paths phải validate fail-closed; snapshot excludes `.git` ở mọi depth, rejects symlink/escape, và deduplicates overlapping roots.
- basis: user-approved governance checkpoint follow-up.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section C.
- supersedes: none

### DEC-013
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: Declared `.git` roots are forbidden; legacy files-only snapshots use fail-closed validated Git fallback instead of ambiguous snapshot comparison.
- basis: user-approved governance checkpoint final follow-up.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section C.
- supersedes: none

### DEC-014
- date: 2026-08-13
- prompt: governance checkpoint
- decision-or-condition: `.git` write-root rejection applies Windows lexical alias normalization using trailing-dot/space removal and case folding per path segment.
- basis: user-approved governance checkpoint final narrow follow-up.
- authority: user governance decision; executable runtime pending verification.
- status: ACCEPTED_BY_USER_PENDING_IMPLEMENTATION_VERIFICATION
- owner: governance/human
- closure evidence: `scripts/prompt_gate.py`; lifecycle tests; transition rules section C.
- supersedes: none
