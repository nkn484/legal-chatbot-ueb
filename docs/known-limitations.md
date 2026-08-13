# Known limitations — Prompt 01.1 snapshot

Snapshot date: **2026-08-13**. The repository contains an orchestration pack, not a runnable Chatbot Pháp luật product.

## Missing runnable product capabilities

- No runnable chatbot or frontend applications are present.
- No backend services are present.
- No API/event contracts are present.
- No database migrations are present.
- No Docker, infrastructure, or deployment configuration is present.
- No CI configuration is present.
- No product unit, integration, contract, security, or E2E test suites are present.

## Not implemented or not measured

No implementation evidence exists for architecture, data ownership, API compatibility, RAG retrieval, publication gating, canonical citations, refusal behavior, provider controls, secret handling, SSRF protection, feedback governance, evaluation, observability, resilience, or release controls. These planned controls must not be treated as implemented merely because their requirements appear in prompt specifications.

The following remain `NOT_MEASURED`:

- Product behavior and service health, because no runnable product is present.
- Architecture/RAG/security invariant enforcement, because relevant code and product tests are absent.
- Secret and repository-history scanning, because no dedicated scanner was run. No secret exposure was confirmed in this safe inventory, but that does not establish a clean secret history.
- Dependency, container, IaC, SAST, and CI scanning, because corresponding product/CI artifacts are absent.

## Risks and conditions

- The missing `.gitignore` increases the risk that future local, generated, or secret-bearing files could be tracked unintentionally.
- The missing exact requested input `00_NGUYEN_TAC_CUNG.md` creates a traceability discrepancy; the available canonical rules are `prompts/00_HARD_RULES.md`.
- The worktree already contained a modified gate state and a deleted ZIP. They must remain outside documentation-writer changes unless their owner explicitly handles them.
- `.opencode/node_modules` is generated tooling material and must not be interpreted as product implementation or compliance evidence.
- Any claim of application compliance with the hard rules requires future implemented artifacts and appropriate validation evidence.
