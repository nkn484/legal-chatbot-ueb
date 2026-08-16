# Architecture acceptance gate — Prompt 02.7 Revision 2

## Conclusion

`PASS_WITH_CONDITIONS_CANDIDATE`: errors and current target blockers are zero. The eight historical blocker records B-001 through B-008 are candidate-resolved only; DEC-005@2 and DEC-007@2 become effective solely on human approval of the current 02.7 revision.

## Candidate evidence

The gate preserves immutable original and preliminary draft baselines, creates `contract-baseline-r2-final.json` once, and validates its sorted current Group 2 hashes on normal runs. `revision-delta-r2.json` records the exact Phase A+B snapshot changes with explicit generated-evidence handling; `compatibility-report-r2.json` references original, preliminary, and final hashes. The final candidate includes current Group 2 contracts, Governance, and the Identity OpenAPI specification while excluding generated reports and gate baselines to avoid recursion.

The current evidence checks a 12-node, 22-edge acyclic synchronous graph including Gateway→Processing; Identity specification/operation/security/headers/examples; five accepted ADRs with Prompt 02.2 lineage; four broker-mediated semantic event deliveries; exact AuditFact active/planned producer sets; and all 14 structured open-field dispositions.

## Conditions

- Human approval is required before candidate decisions are effective.
- Official parsers, generated clients, and broker runtime behavior are `NOT_MEASURED`.
- Critical/High activation remains blocked pending measured evidence.

## Validation

The gate runs Governance, schema, OpenAPI, AsyncAPI, security, lifecycle unittest, and `verify_pack` offline. Its generated report records fresh commands and outcomes, including 30 AsyncAPI messages, 14 channels, 28 operations, 42 security flows, 41 risks, 30 controls, and 70 tests.

## Next prompt

Propose Prompt 03.1 only after human approval of this candidate; do not run it now.
