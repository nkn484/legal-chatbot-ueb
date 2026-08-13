# Repository inventory — Prompt 01.1

Snapshot date: **2026-08-13**. This repository is classified as **`orchestration_pack_only`**. Inventory statuses use only `EXISTS`, `PARTIAL`, `MISSING`, or `UNKNOWN`; planned prompt specifications are not implementation evidence.

## Existing pack/process assets

| Asset | Status | Path-level evidence |
| --- | --- | --- |
| Repository instructions | EXISTS | `AGENTS.md` |
| Canonical hard rules | EXISTS | `prompts/00_HARD_RULES.md` |
| Prompt group specifications | EXISTS | `prompts/groups/01_DIEU_PHOI.md` through `prompts/groups/08_TICH_HOP_NGHIEM_THU.md` |
| Numbered command pack | EXISTS | `.opencode/commands/`; `scripts/verify_pack.py` declares and checks 72 commands |
| Prompt manifest | EXISTS | `prompts/manifest.json` |
| Gate and pack verification tooling | PARTIAL | `scripts/prompt_gate.py`, `scripts/verify_pack.py`; this is pack/process validation, not product validation |
| OMO configuration | EXISTS | `opencode.jsonc`, `.opencode/oh-my-opencode-slim.jsonc`, `.opencode/oh-my-opencode-slim/` |
| Progress-report template | EXISTS | `docs/templates/progress-report.md` |
| Generated tooling dependencies | EXISTS | `.opencode/node_modules/` |
| Git ignore rules | MISSING | `.gitignore` was not found |

**Important:** generated `.opencode/node_modules` is tooling dependency material. It is not product source and is not evidence of product, security, or compliance implementation.

## Missing product artifacts

| Artifact | Status | Evidence |
| --- | --- | --- |
| Chat applications | MISSING | `apps/` is absent; therefore `apps/web-chat/` and `apps/admin-portal/` are absent |
| Backend microservices | MISSING | `services/` is absent; all service paths listed in `AGENTS.md` are absent |
| Versioned API/event contracts | MISSING | `contracts/` is absent |
| Product database migrations | MISSING | No product migration directory or files were discovered in the safe inventory |
| Docker/infra/deployment | MISSING | `infra/` and `deploy/` are absent |
| CI configuration | MISSING | `.github/` is absent |
| Product test suites | MISSING | `tests/` is absent |

The only validation tooling present is partial pack/process tooling. It does not establish a runnable chatbot or validate planned product behavior.

## Prompt-group readiness

| Group | Status | Basis |
| --- | --- | --- |
| 01 | PARTIAL | Orchestration documentation and Prompt 01 specifications exist; this inventory is documentation-only. |
| 02 | MISSING | Architecture and contract work is planned only. |
| 03 | MISSING | Platform, services, deployment, CI, and product tests are planned only. |
| 04 | MISSING | Document, processing, index, and migration work is planned only. |
| 05 | MISSING | Retrieval, provider, citation, and chat work is planned only. |
| 06 | MISSING | Feedback, dataset, and evaluation work is planned only. |
| 07 | MISSING | UI, operations, and hardening work is planned only. |
| 08 | MISSING | Integration, E2E, acceptance, and release work is planned only. |

## Unknown or not-measured security assertions

| Assertion | Status | Caveat |
| --- | --- | --- |
| Confirmed secret exposure | UNKNOWN | No exposure was confirmed during this safe inventory; no candidate secret values were printed. A dedicated secret and history scanner was not run, so assessment remains `NOT_MEASURED`. |
| Secret scanning coverage | UNKNOWN | No dedicated scanner execution evidence is available. |
| Architecture/RAG/security invariant enforcement | UNKNOWN | Product code and relevant product test suites are absent, so enforcement cannot be measured. |
| Environment-file filename inventory | MISSING | No `.env*` filename was discovered in the safe inventory. This does not prove absence of secrets elsewhere. |

## Exact input discrepancy

`prompts/groups/01_DIEU_PHOI.md` requests `00_NGUYEN_TAC_CUNG.md`, but that exact input filename is **MISSING** from the repository. The canonical hard-rules file `prompts/00_HARD_RULES.md` **EXISTS** and was used as the governing source.

## Uncommitted baseline

The initial post-gate-start `git status --short` baseline was:

```text
 M .agent-run/prompt-state.json
 D Chatbot_Phap_luat_OpenCode_OMO_Repo_Pack.zip
```

`.agent-run/prompt-state.json` is gate-managed and was not edited in this lane. The deleted ZIP is treated as a pre-existing/user change and was neither restored nor otherwise modified.
