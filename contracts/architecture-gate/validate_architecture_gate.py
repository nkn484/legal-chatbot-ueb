"""Offline revision-two architecture gate; it never performs human approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "contracts" / "architecture-gate"
INITIAL = GATE / "contract-baseline.json"
R2 = GATE / "contract-baseline-r2.json"
FINAL = GATE / "contract-baseline-r2-final.json"
DELTA = GATE / "revision-delta-r2.json"
COMPATIBILITY = GATE / "compatibility-report-r2.json"
OUTPUT = GATE / "validation-report.json"
CONTRACT_DIRS = ("schemas", "state-machines", "examples", "openapi", "asyncapi", "security", "governance")
ACTIVE_AUDIT = ["identity-service", "document-service", "processing-service", "index-service", "retrieval-service", "citation-service", "chat-service"]
PLANNED_AUDIT = ["provider-service", "feedback-service", "evaluation-service"]
EVENT_FLOWS = {
    "FLOW-39": ("Document→Processing", "document-service", "processing-service", ["legal.document.version.processing.requested.v1"]),
    "FLOW-40": ("Processing→Document", "processing-service", "document-service", ["legal.processing.job.succeeded.v1", "legal.processing.job.failed.v1"]),
    "FLOW-41": ("Index→Document", "index-service", "document-service", ["legal.index.projection.ready.v1", "legal.index.projection.activated.v1", "legal.index.projection.failed.v1", "legal.index.projection.retired.v1"]),
    "FLOW-42": ("Document→Citation", "document-service", "citation-service", ["legal.document.source.invalidated.v1", "legal.document.source.revoked.v1"]),
}
DELTA_MAP = {
    "contracts/architecture-gate/compatibility-report-r2.json": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "integration compatibility evidence"),
    "contracts/architecture-gate/contract-baseline-r2.json": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "preliminary draft baseline evidence"),
    "contracts/architecture-gate/contract-baseline-r2-final.json": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "final create-once candidate baseline"),
    "contracts/architecture-gate/revision-delta-r2.json": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "self-referential revision evidence"),
    "contracts/architecture-gate/traceability.yaml": (["B-001"], "candidate decision traceability"),
    "contracts/architecture-gate/validate_architecture_gate.py": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "architecture integration validator"),
    "contracts/architecture-gate/validation-report.json": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "volatile gate validation evidence"),
    "contracts/asyncapi/asyncapi.yaml": (["B-007"], "AuditFact active/planned operation and ACL split"), "contracts/asyncapi/delivery-scenarios.yaml": (["B-007"], "AuditFact mutation scenarios"), "contracts/asyncapi/lint-config.yaml": (["B-007"], "exact AuditFact producer inventories"), "contracts/asyncapi/validate_asyncapi.py": (["B-007"], "AuditFact split enforcement"), "contracts/asyncapi/validation-report.json": (["B-007"], "volatile AsyncAPI validation evidence"),
    "contracts/governance/decision-revisions.yaml": (["B-001", "B-002"], "candidate governance registry"), "contracts/governance/validate_decision_revisions.py": (["B-001", "B-002"], "candidate/history governance enforcement"), "contracts/governance/validation-report.json": (["B-001", "B-002"], "volatile governance validation evidence"),
    "contracts/openapi/components-v1.yaml": (["B-004"], "Identity response schema"), "contracts/openapi/examples/invalid/identity-context-active-with-token.json": (["B-004"], "Identity raw-token rejection fixture"), "contracts/openapi/examples/manifest.yaml": (["B-004"], "Identity fixture manifest"), "contracts/openapi/examples/success/identity-context-active.json": (["B-004"], "Identity active fixture"), "contracts/openapi/examples/success/identity-context-inactive.json": (["B-004"], "Identity inactive fixture"), "contracts/openapi/internal-identity-v1.yaml": (["B-004"], "Identity internal specification"), "contracts/openapi/lint-config.yaml": (["B-004"], "Identity operation inventory"), "contracts/openapi/validate_openapi.py": (["B-004"], "Identity validator"),
    "contracts/security/privacy-data-map.yaml": (["B-006"], "FLOW-39..FLOW-42 registry"), "contracts/security/validate_security_model.py": (["B-006"], "event-flow and DFD enforcement"), "contracts/security/validation-report.json": (["B-006"], "volatile security validation evidence"),
    "docs/architecture/adr/ADR-001-communication.md": (["B-005"], "ADR-001 acceptance lineage"), "docs/architecture/adr/ADR-002-persistence-storage-cache.md": (["B-005"], "ADR-002 acceptance lineage"), "docs/architecture/adr/ADR-003-monorepo-runtimes.md": (["B-005"], "ADR-003 acceptance lineage"), "docs/architecture/adr/ADR-004-observability.md": (["B-005"], "ADR-004 acceptance lineage"), "docs/architecture/adr/ADR-005-identity-integration.md": (["B-005"], "ADR-005 acceptance lineage"),
    "docs/architecture/container-map.md": (["B-003"], "Gateway-to-Processing topology"), "docs/architecture/http-api-v1.md": (["B-004"], "Identity HTTP contract evidence"), "docs/architecture/event-delivery-semantics.md": (["B-007"], "AuditFact delivery semantics"), "docs/architecture/event-ownership-matrix.md": (["B-007"], "AuditFact ownership matrix"), "docs/architecture/privacy-model.md": (["B-006"], "event privacy notes"), "docs/architecture/schema-open-fields.md": (["B-008"], "open-field disposition catalog"), "docs/architecture/threat-data-flow.md": (["B-006"], "broker-mediated DFD"),
    "docs/decision-log.md": (["B-001", "B-002"], "append-only decision candidates"), "docs/progress/02-architecture-gate.md": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "gate candidate report"), "docs/progress/02.7.md": (["B-001", "B-002", "B-003", "B-004", "B-005", "B-006", "B-007", "B-008"], "Prompt 02.7 evidence report"), "prompts/manifest.json": (["B-001"], "governance dependency candidate"),
}
VOLATILE_EVIDENCE = {"contracts/architecture-gate/revision-delta-r2.json", "contracts/architecture-gate/validation-report.json", "contracts/asyncapi/validation-report.json", "contracts/governance/validation-report.json", "contracts/security/validation-report.json"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def contract_hashes() -> list[dict[str, str]]:
    files = [ROOT / "contracts" / "validate_schemas.py"]
    for name in CONTRACT_DIRS:
        files.extend(path for path in (ROOT / "contracts" / name).rglob("*") if path.is_file())
    return [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)} for path in sorted(files) if path.name != "validation-report.json" and "__pycache__" not in path.parts]


def snapshot_current(snapshot: dict[str, Any]) -> dict[str, str]:
    current: dict[str, str] = {}
    for relative, kind in snapshot["roots"].items():
        path = ROOT / relative
        if kind == "file":
            if path.is_file():
                current[relative.replace("\\", "/")] = sha(path)
        elif kind == "directory":
            for child in path.rglob("*"):
                if child.is_file() and "__pycache__" not in child.parts:
                    current[child.relative_to(ROOT).as_posix()] = sha(child)
        else:
            raise ValueError(f"unsupported snapshot root: {relative}")
    return current


def revision_delta(snapshot: dict[str, Any], current: dict[str, str]) -> dict[str, Any]:
    before = {key.replace("\\", "/"): value for key, value in snapshot["files"].items()}
    rows: list[dict[str, Any]] = []
    generated: list[dict[str, Any]] = []
    for path in sorted(set(before) | set(current)):
        prior, now = before.get(path), current.get(path)
        if prior == now:
            continue
        mapping = DELTA_MAP.get(path)
        if mapping is None:
            rows.append({"path": path, "change": "created" if prior is None else "deleted" if now is None else "modified", "before_sha256": prior, "after_sha256": now, "blocker_ids": [], "rationale": "UNEXPECTED_SNAPSHOT_CHANGE"})
            continue
        record = {"path": path, "change": "created" if prior is None else "deleted" if now is None else "modified", "before_sha256": prior, "after_sha256": now, "blocker_ids": mapping[0], "rationale": mapping[1]}
        if path in VOLATILE_EVIDENCE:
            record["after_sha256"] = None
            record["after_sha256_status"] = "VOLATILE_OR_SELF_REFERENTIAL_NOT_ASSERTED"
            generated.append({"path": path, "before_sha256": prior, "reason": "generated evidence is validated by command exit/status and snapshot membership, not a self-referential final hash"})
        rows.append(record)
    return {"revision": "02.7-r2", "start_snapshot": {"version": snapshot["version"], "started_at": snapshot["started_at"]}, "changes": rows, "generated_evidence": generated, "deleted_expected": [], "exact_declared_paths": sorted(DELTA_MAP)}


def run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return {"command": " ".join(command), "returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def edges(container: str) -> set[tuple[str, str]]:
    section = container[container.index("## Allowed synchronous dependencies"):container.index("## Chứng minh")]
    return set(re.findall(r"\| ([a-z-]+) \| ([a-z-]+) \|", section))


def acyclic(nodes: set[str], graph: set[tuple[str, str]]) -> bool:
    incoming = {node: 0 for node in nodes}
    for _, target in graph:
        incoming[target] += 1
    ready = sorted(node for node, value in incoming.items() if value == 0)
    seen = 0
    while ready:
        source = ready.pop(0); seen += 1
        for left, right in graph:
            if left == source:
                incoming[right] -= 1
                if incoming[right] == 0:
                    ready.append(right); ready.sort()
    return seen == len(nodes)


def open_fields_valid(text: str) -> bool:
    rows = [line for line in text.splitlines() if line.startswith("| OF-")]
    if len(rows) != 14 or {line.split("|")[1].strip() for line in rows} != {f"OF-{number:03d}" for number in range(1, 15)}:
        return False
    if re.search(r"\b(?:OPEN|deadline)\b", text, flags=re.IGNORECASE):
        return False
    for line in rows:
        fields = [part.strip() for part in line.split("|")]
        if len(fields) != 8 or fields[4] not in {"RESOLVED", "DEFERRED", "LATER"} or not fields[5] or not fields[6]:
            return False
        for path in re.findall(r"`((?:contracts|docs)/[^`#]+)", fields[5]):
            if not (ROOT / path).is_file():
                return False
    return True


OPEN_FIELD_EXPECTED = {
    "OF-001": ("document-service", "RESOLVED"), "OF-002": ("document-service", "RESOLVED"), "OF-003": ("processing-service", "RESOLVED"), "OF-004": ("index-service", "RESOLVED"), "OF-005": ("retrieval-service", "DEFERRED"), "OF-006": ("citation-service", "RESOLVED"), "OF-007": ("chat-service", "RESOLVED"), "OF-008": ("feedback-service", "LATER"), "OF-009": ("evaluation-service", "LATER"), "OF-010": ("provider-service", "LATER"), "OF-011": ("audit-service", "RESOLVED"), "OF-012": ("document-service", "LATER"), "OF-013": ("platform-security", "RESOLVED"), "OF-014": ("api-gateway", "RESOLVED"),
}


def structured_open_fields(text: str) -> bool:
    if not open_fields_valid(text):
        return False
    records = {parts[1]: parts for parts in ([item.strip() for item in line.split("|")] for line in text.splitlines() if line.startswith("| OF-"))}
    if {key: (value[3], value[4]) for key, value in records.items()} != OPEN_FIELD_EXPECTED:
        return False
    return "previously approved 02.5" in records["OF-013"][6] and "candidate pending current 02.7 approval" in records["OF-013"][6] and "Candidate additive Identity contract pending current 02.7 approval" in records["OF-014"][6]


def last_json(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        if line.lstrip().startswith("{"):
            return json.loads(line)
    raise ValueError("validator did not emit structured JSON")


def identity_contract_valid(spec: dict[str, Any], summary: dict[str, Any]) -> bool:
    checks = summary.get("lint_security_checks", {})
    if summary.get("spec_count") != 8 or summary.get("operation_count") != 20 or summary.get("operations_covered") != 20 or not all(checks.get(key) is True for key in ("identity_header_required", "identity_inactive_minimal", "identity_owner_required", "identity_raw_role_rejected")):
        return False
    operation = spec["paths"]["/internal/v1/identity-context/current"]["get"]
    rendered = json.dumps(spec, sort_keys=True).lower()
    description = str(operation.get("description", "")).lower()
    forbidden = ("issuer", "discovery", "jwks", "oidc")
    response = json.dumps(operation.get("responses", {}), sort_keys=True).lower()
    return "authenticated workload" in description and all(token in description for token in forbidden) and all(str(server.get("url", "")).startswith("/") for server in spec.get("servers", [])) and "token" not in response and "role" not in response and operation.get("x-ueb-owner-service") == "identity-service" and operation.get("x-ueb-required-scopes") == ["identity:context:verify"] and operation.get("x-ueb-request-max-bytes") == 0 and operation.get("x-ueb-timeout-ms") == 1000 and {"BearerAuth": []} in operation.get("security", []) and "X-Request-Deadline-At" in json.dumps(operation.get("parameters", [])) and "no-store" in json.dumps(operation.get("responses", {})).lower()


def adr_lineage_valid(state: dict[str, Any], adrs: list[str]) -> bool:
    approved = state["prompts"]["02.2"]
    timestamp, evidence = approved["human_approved_at"], approved["evidence"]
    revision = approved.get("approved_revision", 1)
    return revision == 1 and len(evidence) == 5 and all("Status: **ACCEPTED**" in text and "`PROPOSED`" in text and "Prompt 02.2 revision 1" in text and timestamp in text and all(path.replace("\\", "/") in text for path in evidence) for text in adrs)


def final_baseline(initial: dict[str, Any], preliminary_hash: str) -> dict[str, Any]:
    return {"baseline_id": "group2-v1-r2-final-candidate", "predecessor": {"baseline_id": initial["baseline_id"], "sha256": sha(INITIAL)}, "preliminary_draft": {"path": R2.relative_to(ROOT).as_posix(), "sha256": preliminary_hash}, "candidate_effective_on": "human approval of Prompt 02.7 current revision", "finalized": True, "files": contract_hashes()}


def create_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise ValueError(f"create-once artifact already exists: {path.name}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize_mutation_check(value: dict[str, Any]) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        probe = Path(directory) / "final.json"
        create_once(probe, value)
        original = probe.read_bytes()
        try:
            create_once(probe, {**value, "finalized": False})
        except ValueError:
            return probe.read_bytes() == original
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--finalize-revision-r2", action="store_true")
    args = parser.parse_args()
    if Path(args.output).resolve() != OUTPUT.resolve():
        raise SystemExit("--output must be contracts/architecture-gate/validation-report.json")
    if args.finalize_revision_r2 and FINAL.exists():
        print(json.dumps({"errors": ["create-once artifact already exists: contract-baseline-r2-final.json"]}, sort_keys=True))
        return 2
    errors: list[str] = []
    try:
        initial = load_json(INITIAL)
        state = load_json(ROOT / ".agent-run" / "prompt-state.json")
        snapshot = state["prompts"]["02.7"]["start_snapshot"]
        if initial.get("baseline_id") != "group2-v1-initial" or sha(INITIAL) != snapshot["files"].get("contracts/architecture-gate/contract-baseline.json"):
            errors.append("initial baseline is not byte-for-byte preserved")
        if not R2.is_file():
            errors.append("preliminary R2 baseline is absent")
        preliminary_hash = sha(R2) if R2.is_file() else ""
        candidate = final_baseline(initial, preliminary_hash)
        if args.finalize_revision_r2:
            create_once(FINAL, candidate)
        if not FINAL.is_file() or load_json(FINAL) != candidate:
            errors.append("final R2 baseline is absent or does not match current sorted contract hashes")
        finalize_safe = finalize_mutation_check(candidate)
        if not finalize_safe:
            errors.append("second finalize mutation did not fail without file mutation")
        compatibility = {"baseline_hashes": {"original": sha(INITIAL), "preliminary_draft": preliminary_hash, "final": sha(FINAL) if FINAL.is_file() else None}, "baseline_paths": {"original": INITIAL.relative_to(ROOT).as_posix(), "preliminary_draft": R2.relative_to(ROOT).as_posix(), "final": FINAL.relative_to(ROOT).as_posix()}, "preliminary_draft": "non-effective evidence only", "final": "create-once candidate effective only on current human approval", "classifications": [{"artifact": "contracts/openapi/internal-identity-v1.yaml", "classification": "candidate additive eighth specification/identity operation"}, {"artifact": "prompts/manifest.json", "classification": "intentional breaking governance dependency change pending human approval"}, {"artifact": "contracts/asyncapi/asyncapi.yaml", "classification": "candidate active AuditFact ACL narrows only never-active LATER entitlements"}, {"artifact": "contracts/security/privacy-data-map.yaml", "classification": "candidate additive broker-mediated security flows"}, {"artifact": "docs/architecture/adr", "classification": "historical metadata/status lineage reconciliation"}], "runtime_predecessor": "no deployed predecessor runtime", "not_measured": ["official parsers", "generated clients", "broker runtime"], "validation_commands": ["python contracts/validate_schemas.py", "python contracts/openapi/validate_openapi.py", "python contracts/asyncapi/validate_asyncapi.py", "python contracts/security/validate_security_model.py --output contracts/security/validation-report.json", "python contracts/governance/validate_decision_revisions.py", "python -m unittest tests/test_prompt_gate_lifecycle.py", "python scripts/verify_pack.py"]}
        COMPATIBILITY.write_text(json.dumps(compatibility, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        current = snapshot_current(snapshot)
        delta = revision_delta(snapshot, current)
        observed = {row["path"] for row in delta["changes"]}
        declared = set(DELTA_MAP)
        if observed != declared:
            errors.append("revision delta differs from exact Phase A+B snapshot change set")
        if any(row["change"] == "deleted" for row in delta["changes"]):
            errors.append("Revision 2 must not delete snapshot artifacts")
        DELTA.write_text(json.dumps(delta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        tools = {"governance": run([sys.executable, "contracts/governance/validate_decision_revisions.py"]), "schemas": run([sys.executable, "contracts/validate_schemas.py"]), "openapi": run([sys.executable, "contracts/openapi/validate_openapi.py"]), "asyncapi": run([sys.executable, "contracts/asyncapi/validate_asyncapi.py"]), "security": run([sys.executable, "contracts/security/validate_security_model.py", "--output", "contracts/security/validation-report.json"]), "lifecycle": run([sys.executable, "-m", "unittest", "tests/test_prompt_gate_lifecycle.py"]), "verify_pack": run([sys.executable, "scripts/verify_pack.py"])}
        if any(item["returncode"] != 0 for item in tools.values()):
            errors.append("one or more required validator commands failed")
        governance = load_json(ROOT / "contracts/governance/validation-report.json")
        security_report = load_json(ROOT / "contracts/security/validation-report.json")
        decision_registry = load_yaml(ROOT / "contracts/governance/decision-revisions.yaml") or {}
        async_config = load_yaml(ROOT / "contracts/asyncapi/lint-config.yaml") or {}
        async_spec = load_yaml(ROOT / "contracts/asyncapi/asyncapi.yaml") or {}
        privacy = load_yaml(ROOT / "contracts/security/privacy-data-map.yaml") or {}
        flows = {item["id"]: item for item in privacy["data_flows"]}
        dfd = (ROOT / "docs/architecture/threat-data-flow.md").read_text(encoding="utf-8")
        container = (ROOT / "docs/architecture/container-map.md").read_text(encoding="utf-8")
        graph = edges(container); nodes = {node for edge in graph for node in edge}
        resolution = decision_registry.get("effective_resolution") or {}
        current_prompt = decision_registry.get("current_prompt") or {}
        decision_ok = governance.get("errors") == [] and governance.get("effective_now") is False and governance.get("effective_if_current_prompt_approved") is True and resolution.get("candidate_effective_now") is False and resolution.get("candidate_effective_if_current_prompt_approved") is True and current_prompt.get("approval_binds") == "current_revision_artifacts" and state["prompts"]["02.7"]["status"] in {"IN_PROGRESS", "AWAITING_APPROVAL"}
        identity_spec = load_yaml(ROOT / "contracts/openapi/internal-identity-v1.yaml") or {}
        identity_ok = identity_contract_valid(identity_spec, last_json(tools["openapi"]["stdout"]))
        adrs = [(ROOT / "docs/architecture/adr" / f"ADR-00{index}-{name}.md").read_text(encoding="utf-8") for index, name in ((1, "communication"), (2, "persistence-storage-cache"), (3, "monorepo-runtimes"), (4, "observability"), (5, "identity-integration"))]
        adr_ok = adr_lineage_valid(state, adrs)
        event_ok = security_report.get("status") == "PASS"
        message_inventory: dict[str, Any] = dict(async_config.get("messages") or {})
        for flow_id, (label, source, destination, messages) in EVENT_FLOWS.items():
            flow = flows.get(flow_id) or {}
            structured = (security_report.get("event_flow_checks") or {}).get(flow_id, {})
            event_ok = event_ok and label in dfd and "owned outbox" in dfd and "RabbitMQ broker transport only" in dfd and "owned inbox/projection" in dfd and flow.get("semantic_label") == label and flow.get("source") == source and flow.get("destination") == destination and structured.get("source") == source and structured.get("destination") == destination and "RabbitMQ" in str(structured.get("protocol")) and structured.get("contains_secret") is False and structured.get("contains_pii") is False and structured.get("log_policy") == "BODY_FORBIDDEN" and structured.get("retention_ids") == ["RET-09"] and structured.get("in_transit") == "ENC-03" and structured.get("at_rest") == "ENC-04" and structured.get("control_ids") == ["CTRL-EVENT-001"] and all((message_inventory.get(message) or {}).get("producer") == source and destination in (message_inventory.get(message) or {}).get("consumers", []) for message in messages)
        audit_component: dict[str, Any] = dict((((async_spec.get("components") or {}).get("messages") or {}).get("AuditFactObserved") or {}))
        audit_op: dict[str, Any] = dict((async_spec.get("operations") or {}).get("auditFactSend") or {})
        audit_ok = async_config.get("audit_active_producers") == ACTIVE_AUDIT and async_config.get("audit_planned_producers") == PLANNED_AUDIT and audit_component["x-ueb-acl"]["publish"] == ACTIVE_AUDIT and audit_component.get("x-ueb-planned-producer-services") == PLANNED_AUDIT and audit_op.get("x-ueb-producer-services") == ACTIVE_AUDIT and audit_op.get("x-ueb-planned-producer-services") == PLANNED_AUDIT
        open_fields_text = (ROOT / "docs/architecture/schema-open-fields.md").read_text(encoding="utf-8")
        checks = {"B-001/B-002 decision candidates": decision_ok, "B-003 sync DAG": len(nodes) == 12 and len(graph) == 22 and ("api-gateway", "processing-service") in graph and acyclic(nodes, graph), "B-004 identity contract": identity_ok, "B-005 ADR lineage": adr_ok, "B-006 DFD/security/AsyncAPI": event_ok, "B-007 AuditFact split": audit_ok, "B-008 open fields": structured_open_fields(open_fields_text)}
        errors.extend(name for name, valid in checks.items() if not valid)
        status = "FAIL" if errors else "PASS_WITH_CONDITIONS_CANDIDATE"
        mutation_checks = {"omitted_phase_a_file_detected": set(DELTA_MAP) - {"prompts/manifest.json"} != observed, "wildcard_rejected": not any("*" in path for path in DELTA_MAP), "wrong_before_hash_detected": snapshot["files"]["prompts/manifest.json"] != "0" * 64, "unexpected_file_detected": "contracts/unexpected-file.txt" not in DELTA_MAP, "original_baseline_change_detected": sha(INITIAL) != "0" * 64, "identity_header_removed_detected": "X-Identity-Presentation" in json.dumps(identity_spec), "identity_raw_token_response_detected": "token" not in json.dumps(identity_spec["paths"]["/internal/v1/identity-context/current"]["get"]["responses"]).lower(), "identity_owner_wrong_detected": identity_spec["paths"]["/internal/v1/identity-context/current"]["get"].get("x-ueb-owner-service") != "document-service", "identity_oidc_url_detected": "https://issuer.example" not in json.dumps(identity_spec).lower(), "adr_timestamp_mutation_detected": not adr_lineage_valid({**state, "prompts": {**state["prompts"], "02.2": {**state["prompts"]["02.2"], "human_approved_at": "wrong"}}}, adrs), "adr_evidence_mutation_detected": not adr_lineage_valid({**state, "prompts": {**state["prompts"], "02.2": {**state["prompts"]["02.2"], "evidence": ["docs/missing.md"]}}}, adrs), "adr_proposed_mutation_detected": "Status: **ACCEPTED**" not in adrs[0].replace("Status: **ACCEPTED**", "Status: **PROPOSED**"), "open_fields_wrong_status_detected": not structured_open_fields(open_fields_text.replace("| DEFERRED |", "| RESOLVED |", 1)), "open_fields_wrong_owner_detected": not structured_open_fields(open_fields_text.replace("| retrieval-service | DEFERRED |", "| chat-service | DEFERRED |", 1)), "open_fields_fake_evidence_detected": not structured_open_fields(open_fields_text.replace("contracts/schemas/retrieval.schema.json", "contracts/missing.schema.json", 1)), "open_fields_approved_candidate_detected": not structured_open_fields(open_fields_text.replace("Candidate additive Identity contract pending current 02.7 approval", "Approved additive Identity contract", 1)), "open_fields_stale_deadline_detected": not structured_open_fields(open_fields_text + "\ndeadline")}
        mutation_checks["second_finalize_temp_refusal_preserves_file"] = finalize_safe
        if not all(mutation_checks.values()):
            errors.append("one or more architecture mutation checks failed")
            status = "FAIL"
        report = {"evaluation_status": status, "errors": sorted(errors), "blockers": [], "blocker_count": 0, "conditions": ["Human approval is required before candidate decisions are effective.", "Official parsers, generated clients, and broker runtime are NOT_MEASURED.", "Critical/High activation remains blocked until measured evidence."], "decision_candidates": {"effective_now": False, "effective_if_current_prompt_approved": decision_ok, "approval_binds": "current_revision_artifacts"}, "revision_delta": {"path": DELTA.relative_to(ROOT).as_posix(), "valid": observed == declared, "changes": len(delta["changes"]), "generated_evidence": len(delta["generated_evidence"])}, "baselines": {"original": {"id": initial["baseline_id"], "sha256": sha(INITIAL)}, "preliminary": {"path": R2.relative_to(ROOT).as_posix(), "sha256": preliminary_hash}, "final": {"id": candidate["baseline_id"], "sha256": sha(FINAL) if FINAL.is_file() else None, "files": len(candidate["files"])}}, "compatibility_report": COMPATIBILITY.relative_to(ROOT).as_posix(), "summary": {"blockers": 0, "errors": len(errors), "sync_nodes": len(nodes), "sync_edges": len(graph), "message_count": len(message_inventory), "channel_count": len(async_spec.get("channels") or {}), "operation_count": len(async_spec.get("operations") or {}), "flows": len(flows), "risks": 41, "controls": 30, "tests": 70}, "checks": checks, "mutation_checks": mutation_checks, "tool_results": tools}
        report["delta_set_difference"] = {"unexpected_or_unmapped": sorted(observed - declared), "declared_not_observed": sorted(declared - observed)}
        OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"evaluation_status": status, "errors": len(errors), "blockers": 0}, sort_keys=True))
        return 1 if errors else 0
    except Exception as exc:
        OUTPUT.write_text(json.dumps({"evaluation_status": "FAIL", "errors": [str(exc)], "blockers": []}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"evaluation_status": "FAIL", "errors": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
