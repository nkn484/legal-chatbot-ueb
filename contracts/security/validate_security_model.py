"""Offline validator for Prompt 02.6 design registries; it makes no network calls."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.tokens import AliasToken, AnchorToken


ROOT = Path(__file__).resolve().parents[2]
SECURITY = ROOT / "contracts" / "security"
ID_PATTERNS = {"risk": r"RISK-\d{3}", "control": r"CTRL-[A-Z]+-\d{3}", "test": r"SEC-[A-Z]+-\d{3}", "flow": r"FLOW-\d{2}", "boundary": r"TB-\d{2}", "class": r"DC-\d{2}", "retention": r"RET-\d{2}", "encryption": r"ENC-\d{2}"}
SEVERITY = {range(20, 26): "Critical", range(12, 20): "High", range(6, 12): "Medium", range(1, 6): "Low"}
SECRET_LITERAL = re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----|(?i:(?:api[_-]?key|token|secret|password)\s*[:=]\s*[\"']?[A-Za-z0-9+/=_-]{16,})")
CORE_TOPOLOGY = {
    ("public-browser", "api-gateway"), ("admin-browser", "api-gateway"), ("api-gateway", "identity-service"),
    ("api-gateway", "document-service"), ("api-gateway", "processing-service"), ("api-gateway", "audit-service"),
    ("api-gateway", "chat-service"), ("identity-service", "domain-services"), ("document-service", "quarantine-object-store"),
    ("quarantine-object-store", "processing-sandbox"), ("processing-sandbox", "processing-artifact-store"),
    ("domain-services", "broker"), ("broker", "retry-queue"), ("retry-queue", "DLQ"),
    ("document-service", "index-service"), ("chat-service", "retrieval-service"), ("retrieval-service", "index-service"),
    ("retrieval-service", "document-service"), ("retrieval-service", "chat-service"), ("chat-service", "citation-service"),
    ("citation-service", "index-service"), ("citation-service", "document-service"), ("citation-service", "processing-service"),
    ("chat-service", "public-browser"), ("core-audit-producers", "audit-service"), ("all-services", "telemetry-platform"),
    ("service-workloads", "KMS-vault"),
    ("document-service", "processing-service"), ("processing-service", "document-service"),
    ("index-service", "document-service"), ("document-service", "citation-service"),
}
DB_SERVICES = {"identity-service", "audit-service", "document-service", "processing-service", "index-service", "retrieval-service", "provider-service", "citation-service", "chat-service", "feedback-service", "evaluation-service"}


class StrictLoader(yaml.SafeLoader):
    """Safe loader that rejects YAML aliases, merges, duplicate keys, and non-string keys."""


def _construct_mapping(loader: StrictLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ConstructorError("while constructing a mapping", node.start_mark, "mapping key must be a string", key_node.start_mark)
        if key == "<<":
            raise ConstructorError("while constructing a mapping", node.start_mark, "YAML merge keys are prohibited", key_node.start_mark)
        if key in result:
            raise ConstructorError("while constructing a mapping", node.start_mark, f"duplicate key: {key}", key_node.start_mark)
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    for token in yaml.scan(text):
        if isinstance(token, (AnchorToken, AliasToken)):
            raise ValueError(f"{path.name}: YAML anchors and aliases are prohibited")
    value = yaml.load(text, Loader=StrictLoader)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: root must be a mapping")
    return value


def ids(items: list[dict[str, Any]], pattern: str, label: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for item in items:
        ident = item.get("id") if isinstance(item, dict) else None
        if not isinstance(ident, str) or not re.fullmatch(pattern, ident):
            errors.append(f"invalid {label} ID: {ident!r}")
        elif ident in seen:
            errors.append(f"duplicate {label} ID: {ident}")
        else:
            seen.add(ident)
    return seen


def expected_severity(score: int) -> str | None:
    for score_range, severity in SEVERITY.items():
        if score in score_range:
            return severity
    return None


def require_refs(values: Any, allowed: set[str], owner: str, label: str, errors: list[str]) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"{owner}: missing {label}")
        return
    unknown = set(values) - allowed
    if unknown:
        errors.append(f"{owner}: unknown {label}: {sorted(unknown)}")


def check_model(model: dict[str, Any], docs: dict[str, str] | None = None) -> list[str]:
    errors: list[str] = []
    risks, controls, tests, privacy = model["risks"], model["controls"], model["tests"], model["privacy"]
    risk_ids = ids(risks, ID_PATTERNS["risk"], "risk", errors)
    control_ids = ids(controls, ID_PATTERNS["control"], "control", errors)
    test_ids = ids(tests, ID_PATTERNS["test"], "test", errors)
    boundary_ids = ids(privacy["trust_boundaries"], ID_PATTERNS["boundary"], "boundary", errors)
    class_ids = ids(privacy["data_classes"], ID_PATTERNS["class"], "class", errors)
    retention_ids = ids(privacy["retention_rules"], ID_PATTERNS["retention"], "retention", errors)
    encryption_ids = ids(privacy["encryption_registry"], ID_PATTERNS["encryption"], "encryption", errors)
    flow_ids = ids(privacy["data_flows"], ID_PATTERNS["flow"], "flow", errors)
    if len(risks) != 41: errors.append(f"expected 41 risks, got {len(risks)}")
    if risk_ids != {f"RISK-{n:03d}" for n in range(1, 42)}: errors.append("RISK-001..RISK-041 exact coverage required")
    if len(tests) != 70: errors.append(f"expected 70 tests, got {len(tests)}")
    if len(privacy["trust_boundaries"]) < 13 or not {f"TB-{n:02d}" for n in range(1, 14)} <= boundary_ids: errors.append("TB-01..TB-13 required")
    if len(class_ids) < 12 or len(encryption_ids) < 12 or len(flow_ids) != 42: errors.append("privacy registry must contain exactly 42 flows")
    for risk in risks:
        ident = risk.get("id", "<unknown>")
        score = risk.get("score")
        if not isinstance(risk.get("likelihood"), int) or not isinstance(risk.get("impact"), int) or score != risk.get("likelihood") * risk.get("impact"):
            errors.append(f"{ident}: score must equal likelihood * impact")
        if risk.get("severity") != expected_severity(score) if isinstance(score, int) else True:
            errors.append(f"{ident}: severity does not match score")
        if risk.get("current_status") != "OPEN_PLANNED" or risk.get("risk_acceptance") != "NOT_ACCEPTED": errors.append(f"{ident}: all risks must remain OPEN_PLANNED and NOT_ACCEPTED")
        require_refs(risk.get("control_ids"), control_ids, ident, "control refs", errors)
        require_refs(risk.get("test_ids"), test_ids, ident, "test refs", errors)
        require_refs(risk.get("trust_boundary_ids"), boundary_ids, ident, "boundary refs", errors)
        if risk.get("severity") in {"Critical", "High"}:
            required = {"owner", "acceptance_criteria", "evidence_required"}
            if any(not risk.get(field) for field in required) or risk.get("verification_status") != "NOT_MEASURED" or risk.get("activation_gate") != "BLOCKED_UNTIL_VERIFIED" or risk.get("target_residual") not in {"MEDIUM", "LOW"}:
                errors.append(f"{ident}: Critical/High activation evidence incomplete")
    required_areas = {"admin-publish", "api-authorization", "upload-parser", "rag-corpus", "retrieval-eligibility", "citation-integrity", "provider-ssrf", "privacy-data-handling", "feedback-governance", "event-security", "supply-chain", "resource-exhaustion", "source-connector"}
    if not required_areas <= {risk.get("area") for risk in risks}:
        errors.append("required risk areas/topics missing")
    for control in controls:
        require_refs(control.get("verification_test_ids"), test_ids, control.get("id", "<unknown>"), "test refs", errors)
    for test in tests:
        if test.get("status") != "PLANNED_NOT_RUN" or "FAIL_CLOSED" not in str(test.get("expected_result")) or not test.get("evidence_artifact"):
            errors.append(f"{test.get('id')}: must be PLANNED_NOT_RUN with FAIL_CLOSED evidence")
        core_test_text = " ".join(str(test.get(field, "")) for field in ("title", "preconditions", "attack_inputs")).lower()
        if test.get("phase") == "CORE" and ("backup" in core_test_text or "restore" in core_test_text):
            errors.append(f"{test.get('id')}: backup/restore test cannot be Core")
    tests_by_id = {test.get("id"): test for test in tests}
    later_test_ids = {test_id for test_id, test in tests_by_id.items() if test.get("phase") == "LATER"}
    for entity_type, entities, field in (("risk", risks, "test_ids"), ("control", controls, "verification_test_ids")):
        for entity in entities:
            if entity.get("phase") in {"CORE", "BOTH"} and (any(tests_by_id.get(test_id, {}).get("phase") == "LATER" for test_id in entity.get(field, [])) or any(test_id in json.dumps(entity, ensure_ascii=False) for test_id in later_test_ids)):
                errors.append(f"{entity.get('id')}: Core-applicable {entity_type} cannot reference a LATER test")
    stride = {x for risk in risks for x in risk.get("stride", [])}
    llm = {x for risk in risks for x in risk.get("owasp_llm_2025", [])}
    api = {x for risk in risks for x in risk.get("owasp_api_2023", [])}
    if stride != {"S", "T", "R", "I", "D", "E"}: errors.append("complete STRIDE coverage required")
    if llm != {f"LLM{n:02d}" for n in range(1, 11)}: errors.append("complete OWASP LLM01..LLM10 coverage required")
    if api != {f"API{n}" for n in range(1, 11)}: errors.append("complete OWASP API1..API10 coverage required")
    r38 = next((r for r in risks if r.get("id") == "RISK-038"), {})
    if "LLM10" not in r38.get("owasp_llm_2025", []): errors.append("RISK-038 must map LLM10")
    event = next((c for c in controls if c.get("id") == "CTRL-EVENT-001"), {})
    event_text = str(event.get("implementation_requirement", "")).lower()
    if "signed envelope" in event_text or "broker mtls connection" not in event_text or "payload hash provides integrity only" not in event_text:
        errors.append("CTRL-EVENT-001 must use broker mTLS/ACL producer authentication, not signed envelope")
    for flow in privacy["data_flows"]:
        ident = flow.get("id", "<unknown>")
        required = {"source", "destination", "protocol", "data_class_ids", "owner", "phase", "trust_boundaries", "purpose", "minimization", "in_transit", "at_rest", "contains_secret", "contains_pii", "log_policy", "retention_ids", "control_ids", "external", "default_state"}
        missing = [field for field in required if field not in flow or flow[field] in (None, "", [])]
        if missing: errors.append(f"{ident}: missing flow fields {missing}")
        require_refs(flow.get("data_class_ids"), class_ids, ident, "data class refs", errors)
        require_refs(flow.get("retention_ids"), retention_ids, ident, "retention refs", errors)
        require_refs(flow.get("control_ids"), control_ids, ident, "control refs", errors)
        require_refs(flow.get("trust_boundaries"), boundary_ids, ident, "boundary refs", errors)
        if (flow.get("contains_pii") or flow.get("contains_secret")) and flow.get("log_policy") != "BODY_FORBIDDEN": errors.append(f"{ident}: sensitive flow must forbid body logging")
        if flow.get("in_transit") not in encryption_ids or flow.get("at_rest") not in encryption_ids:
            errors.append(f"{ident}: in_transit and at_rest must reference encryption entries")
        if flow.get("phase") == "CORE" and (flow.get("source"), flow.get("destination")) not in CORE_TOPOLOGY:
            errors.append(f"{ident}: Core topology edge is not approved")
        if (flow.get("source"), flow.get("destination")) in {("retrieval-service", "citation-service"), ("broker", "retrieval-service")}:
            errors.append(f"{ident}: prohibited Retrieval→Citation or broker→Retrieval topology")
        if flow.get("phase") == "LATER" and flow.get("default_state") != "DENIED_NOT_SENT":
            errors.append(f"{ident}: every LATER flow must be DENIED_NOT_SENT")
        if "oidc" in f"{flow.get('source')} {flow.get('destination')} {flow.get('elements')}".lower() or "jwks" in f"{flow.get('source')} {flow.get('destination')} {flow.get('elements')}".lower():
            if flow.get("phase") != "LATER": errors.append(f"{ident}: live OIDC/JWKS cannot be a Core flow")
    for rule in privacy["retention_rules"]:
        required = {"owner", "data_classes", "purpose", "trigger", "effective_limit_rule", "deletion_method", "propagation", "legal_hold_authority", "legal_hold_rule", "test_ids", "lawful_basis_status"}
        if any(not rule.get(field) for field in required): errors.append(f"{rule.get('id')}: incomplete retention rule")
    exact_retention = {"RET-01": (7, "days"), "RET-02": (24, "hours"), "RET-03": (15, "minutes"), "RET-04": (7, "days"), "RET-07": (14, "days"), "RET-08": (30, "days"), "RET-09": (24, "hours"), "RET-10": (7, "days"), "RET-11": (30, "days")}
    for ident, expected in exact_retention.items():
        rule = next((r for r in privacy["retention_rules"] if r.get("id") == ident), {})
        if (rule.get("max_value"), rule.get("unit")) != expected: errors.append(f"{ident}: incorrect effective retention maximum")
    ret11 = next((r for r in privacy["retention_rules"] if r.get("id") == "RET-11"), {})
    if ret11.get("lifecycle") != "NOT_COLLECTED_CORE" or ret11.get("lawful_basis_status") != "FUTURE_SCHEDULE_REQUIRED" or (ret11.get("max_value"), ret11.get("unit")) != (30, "days"):
        errors.append("RET-11 must be future 30d max and NOT_COLLECTED_CORE")
    for entry in privacy["encryption_registry"]:
        required = {"location", "algorithm_protocol", "key_alias_pattern", "key_owner", "service_principal", "access_export_rule", "rotation", "compromise", "recovery", "status"}
        if any(not entry.get(field) for field in required) or entry.get("status") != "PLANNED_NOT_IMPLEMENTED": errors.append(f"{entry.get('id')}: incomplete encryption entry")
        if str(entry.get("algorithm_protocol", "")).lower() in {"encrypted", "tls", "kms"}: errors.append(f"{entry.get('id')}: vague encryption is not sufficient")
    enc08 = next((e for e in privacy["encryption_registry"] if e.get("id") == "ENC-08"), {})
    mappings = enc08.get("service_mappings", [])
    mapped_services = {m.get("service") for m in mappings if isinstance(m, dict)}
    aliases = [m.get("kms_alias") for m in mappings if isinstance(m, dict)]
    principals = [m.get("workload_principal") for m in mappings if isinstance(m, dict)]
    if mapped_services != DB_SERVICES or len(mappings) != len(DB_SERVICES) or "api-gateway" in mapped_services or len(set(aliases)) != len(aliases) or len(set(principals)) != len(principals):
        errors.append("ENC-08 requires exact unique state-owning service mappings and no gateway DB")
    if any(not all(m.get(key) for key in ("store_location", "kms_alias", "data_owner", "workload_principal")) for m in mappings if isinstance(m, dict)):
        errors.append("ENC-08 service mapping fields incomplete")
    if any(word in json.dumps(enc08, ensure_ascii=False).lower() for word in ("{service}", "service-specific", "generic")):
        errors.append("ENC-08 rejects template or generic key mapping labels")
    flow_by_id = {flow.get("id"): flow for flow in privacy["data_flows"]}
    expected_event_flows = {
        "FLOW-39": ("Document→Processing", "document-service", "processing-service", "processing-requested"),
        "FLOW-40": ("Processing→Document", "processing-service", "document-service", "processing-outcome"),
        "FLOW-41": ("Index→Document", "index-service", "document-service", "index-projection-outcome"),
        "FLOW-42": ("Document→Citation", "document-service", "citation-service", "document-source-invalidated-revoked"),
    }
    for ident, (label, source, destination, purpose) in expected_event_flows.items():
        flow = flow_by_id.get(ident, {})
        if (flow.get("semantic_label"), flow.get("source"), flow.get("destination"), flow.get("purpose")) != (label, source, destination, purpose) or flow.get("owner") != source or flow.get("protocol") != "AMQP-0-9-1-via-RabbitMQ" or flow.get("data_class_ids") != ["DC-10"] or flow.get("retention_ids") != ["RET-09"] or flow.get("control_ids") != ["CTRL-EVENT-001"] or flow.get("at_rest") != "ENC-04" or flow.get("contains_secret") or flow.get("contains_pii") or flow.get("default_state") != "ACTIVE_DESIGN_ONLY":
            errors.append(f"{ident}: exact broker-mediated safe event flow required")
        if flow.get("in_transit") != "ENC-03" or "body" in str(flow.get("elements", "")).lower() or flow.get("log_policy") != "BODY_FORBIDDEN":
            errors.append(f"{ident}: event transport/body minimization required")
    audit_flow = flow_by_id.get("FLOW-20", {})
    if audit_flow.get("source") != "core-audit-producers" or audit_flow.get("protocol") != "AMQP-0-9-1-via-RabbitMQ" or any(name not in str(audit_flow.get("elements", "")) for name in ("identity", "document", "processing", "index", "retrieval", "citation", "chat")):
        errors.append("FLOW-20 must identify only active Core AuditFact producers")
    for ident in ("FLOW-22", "FLOW-23"):
        flow = flow_by_id.get(ident, {})
        if flow.get("phase") != "LATER" or flow.get("default_state") != "DENIED_NOT_SENT": errors.append(f"{ident}: backup/DR must be LATER denied")
        if flow.get("control_ids") != ["CTRL-PRIV-003", "CTRL-KEY-001"]: errors.append(f"{ident}: backup/DR must use LATER backup controls")
    flow26 = flow_by_id.get("FLOW-26", {})
    if flow26.get("phase") != "LATER" or "CTRL-PRIV-004" not in flow26.get("control_ids", []) or "CTRL-PRIV-001" in flow26.get("control_ids", []):
        errors.append("FLOW-26 must use LATER Provider privacy control, not Core privacy control")
    core_kms = flow_by_id.get("FLOW-24", {})
    if core_kms.get("phase") != "CORE" or core_kms.get("data_class_ids") != ["DC-16"] or core_kms.get("contains_secret") or core_kms.get("at_rest") == "ENC-12" or "RET-13" in core_kms.get("retention_ids", []) or any(control.startswith(("CTRL-PROVIDER", "CTRL-SOURCE")) for control in core_kms.get("control_ids", [])):
        errors.append("FLOW-24 must remain Core cryptographic metadata only")
    for ident, class_id, encryption, retention in (("FLOW-37", "DC-13", "ENC-12", "RET-13"), ("FLOW-38", "DC-17", "ENC-16", "RET-17")):
        flow = flow_by_id.get(ident, {})
        if flow.get("phase") != "LATER" or flow.get("default_state") != "DENIED_NOT_SENT" or class_id not in flow.get("data_class_ids", []) or flow.get("at_rest") != encryption or retention not in flow.get("retention_ids", []):
            errors.append(f"{ident}: secret flow must be separate LATER denied flow")
    risks_by_id = {risk.get("id"): risk for risk in risks}
    controls_by_id = {control.get("id"): control for control in controls}
    if any(risks_by_id.get(ident, {}).get("phase") != "LATER" or risks_by_id.get(ident, {}).get("control_ids") != ["CTRL-AUTH-005"] for ident in ("RISK-005", "RISK-006")):
        errors.append("OIDC/JWKS risks must be LATER with CTRL-AUTH-005")
    if any(tests_by_id.get(ident, {}).get("phase") != "LATER" for ident in ("SEC-AUTH-008", "SEC-AUTH-009")) or tests_by_id.get("SEC-AUTH-010", {}).get("phase") != "CORE" or controls_by_id.get("CTRL-AUTH-005", {}).get("phase") != "LATER":
        errors.append("OIDC/JWKS tests/control must be LATER while workload identity remains Core")
    if tests_by_id.get("SEC-PRIV-006", {}).get("phase") != "LATER":
        errors.append("SEC-PRIV-006 backup restore/deletion-ledger test must be LATER")
    r24, r25, r41 = risks_by_id.get("RISK-024", {}), risks_by_id.get("RISK-025", {}), risks_by_id.get("RISK-041", {})
    priv1, priv2, priv3, priv4 = controls_by_id.get("CTRL-PRIV-001", {}), controls_by_id.get("CTRL-PRIV-002", {}), controls_by_id.get("CTRL-PRIV-003", {}), controls_by_id.get("CTRL-PRIV-004", {})
    if priv1.get("phase") != "CORE" or priv1.get("verification_test_ids") != ["SEC-PRIV-001", "SEC-PRIV-002", "SEC-PRIV-004"] or "SEC-PRIV-003" in json.dumps(priv1, ensure_ascii=False) or any(term in json.dumps(priv1, ensure_ascii=False).lower() for term in ("provider", "external export")):
        errors.append("CTRL-PRIV-001 must be Core-only and exclude Provider privacy egress")
    if priv4.get("phase") != "LATER" or priv4.get("verification_test_ids") != ["SEC-PRIV-003"]:
        errors.append("CTRL-PRIV-004 must be LATER-only with SEC-PRIV-003")
    if r24.get("phase") != "LATER" or "CTRL-PRIV-004" not in r24.get("control_ids", []) or "CTRL-PRIV-001" in r24.get("control_ids", []):
        errors.append("RISK-024 must use LATER Provider privacy control")
    if r25.get("phase") != "CORE" or "SEC-PRIV-006" in r25.get("test_ids", []) or any(term in json.dumps(r25, ensure_ascii=False).lower() for term in ("backup", "provider", "restore")):
        errors.append("RISK-025 must be Core-only and exclude backup/provider/restore and SEC-PRIV-006")
    if r41.get("phase") != "LATER" or r41.get("control_ids") != ["CTRL-PRIV-003", "CTRL-KEY-001"] or r41.get("test_ids") != ["SEC-PRIV-006"] or priv3.get("phase") != "LATER" or priv3.get("verification_test_ids") != ["SEC-PRIV-006"]:
        errors.append("RISK-041/CTRL-PRIV-003/SEC-PRIV-006 LATER linkage required")
    if priv2.get("phase") != "CORE" or priv2.get("verification_test_ids") != ["SEC-PRIV-005"] or any(term in json.dumps(priv2, ensure_ascii=False).lower() for term in ("backup", "restore")):
        errors.append("CTRL-PRIV-002 must be Core-only deletion propagation")
    for rule in privacy["retention_rules"]:
        is_future = rule.get("id") == "RET-11" or str(rule.get("purpose", "")).startswith("future-") or rule.get("lifecycle") in {"NOT_SENT", "NOT_COLLECTED_CORE"} or rule.get("lawful_basis_status") == "FUTURE_SCHEDULE_REQUIRED"
        if not is_future and ("SEC-PRIV-006" in rule.get("test_ids", []) or "backup" in str(rule.get("propagation", "")).lower() or "restore" in str(rule.get("propagation", "")).lower()):
            errors.append(f"{rule.get('id')}: Core retention cannot reference backup/restore or SEC-PRIV-006")
    for registry_name, registry in (("risks", risks), ("controls", controls), ("tests", tests), ("privacy", privacy)):
        if SECRET_LITERAL.search(json.dumps(registry, ensure_ascii=False)):
            errors.append(f"{registry_name}: token-like secret literal or private key is prohibited")
    if docs is not None:
        threat, dfd, privacy_doc = docs["threat"], docs["dfd"], docs["privacy"]
        for risk in risks:
            if risk.get("severity") in {"Critical", "High"} and risk["id"] not in threat: errors.append(f"threat model missing {risk['id']}")
        for flow in privacy["data_flows"]:
            if flow["id"] not in dfd: errors.append(f"DFD missing {flow['id']}")
        if any(word not in threat for word in ("NOT_MEASURED", "NOT_ACCEPTED", "DEC-005", "OWASP", "API1", "API10", "API6", "REQ-OPS-002", "local/demo", "LATER")): errors.append("threat model required warning/reference missing")
        if "not legal advice" not in privacy_doc.lower() or "HUMAN_APPROVAL_REQUIRED" not in privacy_doc: errors.append("privacy model legal approval warning missing")
        event_labels = ("Document→Processing", "Processing→Document", "Index→Document", "Document→Citation")
        if any(edge not in dfd for edge in ("C --> CT", "R --> C", "CT --> IX", "RabbitMQ broker transport only", "owned outbox", "owned inbox/projection", *event_labels)) or any(edge in dfd for edge in ("B --> R", "R --> CT", "D --> P", "P --> D", "IX --> D", "D --> CT")):
            errors.append("DFD topology does not match approved Citation/Retrieval/event paths")
        if "REQ-OPS-002" not in privacy_doc or "NOT_COLLECTED_CORE" not in privacy_doc:
            errors.append("privacy model must record LATER backup/DR exclusion")
    return errors


def mutation_checks(model: dict[str, Any]) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    base = check_model(model)
    cases = {
        "missing_risk_owner": ("risks", 0, "owner", None), "missing_risk_control": ("risks", 0, "control_ids", []), "missing_risk_test": ("risks", 0, "test_ids", []), "wrong_score_severity": ("risks", 0, "score", 99),
        "critical_accepted": ("risks", 0, "risk_acceptance", "ACCEPTED"), "test_pass": ("tests", 0, "status", "PASS"), "backup_test_core": ("tests", 42, "phase", "CORE"), "core_risk_later_test": ("risks", 24, "__append_to__", ("test_ids", "SEC-PRIV-006")), "core_control_later_test": ("controls", 16, "__append_to__", ("verification_test_ids", "SEC-PRIV-006")), "core_retention_later_test": ("privacy.retention_rules", 0, "__append_to__", ("test_ids", "SEC-PRIV-006")), "core_privacy_provider_test": ("controls", 15, "__append_to__", ("verification_test_ids", "SEC-PRIV-003")),
        "missing_llm_category": ("risks", 25, "owasp_llm_2025", []), "pii_flow_missing_retention": ("privacy.data_flows", 0, "retention_ids", []),
        "provider_flow_active": ("privacy.data_flows", 24, "default_state", "ACTIVE"), "feedback_flow_active": ("privacy.data_flows", 26, "default_state", "ACTIVE"), "evaluation_flow_active": ("privacy.data_flows", 27, "default_state", "ACTIVE"), "source_flow_active": ("privacy.data_flows", 28, "default_state", "ACTIVE"), "backup_flow_active": ("privacy.data_flows", 21, "default_state", "ACTIVE"), "retrieval_to_citation": ("privacy.data_flows", 15, "source", "retrieval-service"), "broker_to_retrieval": ("privacy.data_flows", 34, "__edge__", ("broker", "retrieval-service")), "retention_above_max": ("privacy.retention_rules", 8, "max_value", 25),
        "missing_event_direction": ("privacy.data_flows", 38, "destination", "index-service"), "direct_db_arrow": ("privacy.data_flows", 38, "destination", "processing-service-db"), "broker_as_owner": ("privacy.data_flows", 38, "owner", "broker"), "event_body_injected": ("privacy.data_flows", 38, "elements", "body"), "event_pii_injected": ("privacy.data_flows", 38, "contains_pii", True),
        "vague_encryption": ("privacy.encryption_registry", 0, "algorithm_protocol", "encrypted"), "missing_key_owner": ("privacy.encryption_registry", 0, "key_owner", ""),
        "hold_missing_authority": ("privacy.retention_rules", 0, "legal_hold_authority", ""),
    }
    for name, (path, index, field, value) in cases.items():
        trial = copy.deepcopy(model)
        target: Any = trial
        for part in path.split("."):
            target = target[part]
        if field == "__edge__":
            target[index]["source"], target[index]["destination"] = value
        elif field == "__append_to__":
            target[index][value[0]].append(value[1])
        else:
            target[index][field] = value
        checks[name] = bool(check_model(trial)) and not base
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if output.parent != SECURITY.resolve() or output.suffix != ".json":
        parser.error("--output must be a repository-relative JSON path directly under contracts/security")
    try:
        model = {"risks": load_yaml(SECURITY / "risk-register.yaml")["risks"], "controls": load_yaml(SECURITY / "security-controls.yaml")["controls"], "tests": load_yaml(SECURITY / "security-tests.yaml")["tests"], "privacy": load_yaml(SECURITY / "privacy-data-map.yaml")}
        docs = {"threat": (ROOT / "docs/architecture/threat-model.md").read_text(encoding="utf-8"), "dfd": (ROOT / "docs/architecture/threat-data-flow.md").read_text(encoding="utf-8"), "privacy": (ROOT / "docs/architecture/privacy-model.md").read_text(encoding="utf-8")}
        errors = check_model(model, docs)
        mutations = mutation_checks(model)
        if not all(mutations.values()): errors.append("one or more negative mutation checks did not fail validation")
        risks = model["risks"]
        flows = model["privacy"]["data_flows"]
        input_paths = [SECURITY / name for name in ("risk-register.yaml", "security-controls.yaml", "security-tests.yaml", "privacy-data-map.yaml")] + [ROOT / "docs/architecture" / name for name in ("threat-model.md", "threat-data-flow.md", "privacy-model.md")]
        hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths}
        later = [f for f in flows if f["phase"] == "LATER" and f["default_state"] == "DENIED_NOT_SENT"]
        flows_by_id = {flow["id"]: flow for flow in flows}
        event_flow_checks = {flow_id: {"semantic_label": flows_by_id[flow_id]["semantic_label"], "source": flows_by_id[flow_id]["source"], "destination": flows_by_id[flow_id]["destination"], "protocol": flows_by_id[flow_id]["protocol"], "contains_secret": flows_by_id[flow_id]["contains_secret"], "contains_pii": flows_by_id[flow_id]["contains_pii"], "log_policy": flows_by_id[flow_id]["log_policy"], "retention_ids": flows_by_id[flow_id]["retention_ids"], "in_transit": flows_by_id[flow_id]["in_transit"], "at_rest": flows_by_id[flow_id]["at_rest"], "control_ids": flows_by_id[flow_id]["control_ids"]} for flow_id in ("FLOW-39", "FLOW-40", "FLOW-41", "FLOW-42")}
        report = {"status": "PASS" if not errors else "FAIL", "input_sha256": hashes, "counts": {"risks": len(risks), "severity": {s: sum(r["severity"] == s for r in risks) for s in ("Critical", "High", "Medium", "Low")}, "phase": {p: sum(r["phase"] == p for r in risks) for p in ("CORE", "LATER", "BOTH")}, "critical_high_coverage": sum(r["severity"] in {"Critical", "High"} for r in risks), "controls": len(model["controls"]), "tests": len(model["tests"]), "boundaries": len(model["privacy"]["trust_boundaries"]), "flows": len(flows), "classes": len(model["privacy"]["data_classes"]), "retention": len(model["privacy"]["retention_rules"]), "encryption": len(model["privacy"]["encryption_registry"]), "pii_flows": sum(f["contains_pii"] for f in flows), "secret_flows": sum(f["contains_secret"] for f in flows), "external_flows": sum(f["external"] for f in flows), "later_denied_flows": len(later), "later_denied_families": {"backup_dr": sum(f["id"] in {"FLOW-22", "FLOW-23"} for f in later), "provider": sum(f["id"] in {"FLOW-25", "FLOW-26", "FLOW-37"} for f in later), "feedback_evaluation": sum(f["id"] in {"FLOW-27", "FLOW-28"} for f in later), "source": sum(f["id"] in {"FLOW-29", "FLOW-30", "FLOW-38"} for f in later)}, "stride": sorted({x for r in risks for x in r["stride"]}), "owasp_llm": sorted({x for r in risks for x in r["owasp_llm_2025"]}), "owasp_api": sorted({x for r in risks for x in r["owasp_api_2023"]})}, "event_flow_checks": event_flow_checks, "mutation_checks": mutations, "errors": errors}
        output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        output.write_text(json.dumps({"status": "FAIL", "errors": [str(exc)]}, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return 1
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
