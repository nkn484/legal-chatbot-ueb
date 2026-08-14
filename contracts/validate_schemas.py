"""Offline validation affordance for Prompt 02.3 exchange schemas and fixtures."""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urldefrag, urljoin, urlparse

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import PointerToNowhere, Unresolvable


ROOT = Path(__file__).resolve().parent
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples"
CATALOG = ROOT / "state-machines" / "domain-state-machines.v1.json"
NAMESPACE = "https://schemas.example.invalid/legal-chatbot/v1/"
SCHEMA_NAMES = (
    "common.schema.json", "status.schema.json", "document.schema.json",
    "processing.schema.json", "index.schema.json", "retrieval.schema.json",
    "chat.schema.json", "citation.schema.json", "provider-config-view.schema.json",
    "feedback.schema.json", "evaluation.schema.json", "error.schema.json",
    "state-machine.schema.json", "source-connector-port.schema.json",
)
EXPECTED_CONCEPTS = (
    "Document", "Version", "Job", "Chunk", "IndexProjection", "RetrievalRun",
    "Chat", "GroundedAnswer", "Citation", "ProviderConfigView", "Feedback",
    "GoldenAnswer", "Dataset", "Evaluation", "Candidate", "SourceSystem",
)
STATE_SOURCES = {
    "Document": ("document.schema.json", "Document", "status"),
    "Version": ("document.schema.json", "Version", "status"),
    "Job": ("processing.schema.json", "Job", "status"),
    "Chunk": ("processing.schema.json", "Chunk", "status"),
    "IndexProjection": ("index.schema.json", "IndexProjection", "status"),
    "RetrievalRun": ("retrieval.schema.json", "RetrievalRun", "state"),
    "Chat": ("chat.schema.json", "Chat", "status"),
    "GroundedAnswer": ("chat.schema.json", "GroundedAnswer", "outcome"),
    "Citation": ("citation.schema.json", "Citation", "validation_status"),
    "ProviderConfigView": ("provider-config-view.schema.json", "ProviderConfigView", "status"),
    "Feedback": ("feedback.schema.json", "Feedback", "status"),
    "GoldenAnswer": ("feedback.schema.json", "GoldenAnswer", "status"),
    "Dataset": ("evaluation.schema.json", "Dataset", "status"),
    "Evaluation": ("evaluation.schema.json", "Evaluation", "status"),
    "Candidate": ("evaluation.schema.json", "Candidate", "status"),
    "SourceSystem": ("source-connector-port.schema.json", "SourceSystem", "lifecycle_status"),
}
FORBIDDEN_PROVIDER_KEYS = (
    "secret", "api_key", "apikey", "token", "password", "credential",
    "private_key", "access_key", "refresh_key", "bearer", "authorization",
)
FORBIDDEN_GROUNDED_TOKENS = (
    "url", "canonical", "official_title", "title", "document_number", "page",
    "locator", "excerpt", "provider", "citation", "source", "render",
)
FORBIDDEN_SOURCE_KEYS = (
    "secret", "api_key", "apikey", "token", "password", "credential",
    "private_key", "access_key", "refresh_key", "bearer", "authorization",
)
MUTATION_TOKENS = (
    "create", "update", "remove", "delete", "write", "add", "insert", "save",
    "set", "publish", "upsert", "patch", "post", "put",
)
VBQPPL_ENDPOINT = "https://ws.vbpl.vn/vbqppl.asmx"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def walk_refs(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        if isinstance(value.get("$ref"), str):
            yield value["$ref"]
        for nested in value.values():
            yield from walk_refs(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_refs(nested)


def walk_property_keys(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            yield from properties
        for nested in value.values():
            yield from walk_property_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_property_keys(nested)


def walk_instance_keys(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from walk_instance_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_instance_keys(nested)


def flatten_errors(errors: Iterable[Any]) -> Iterable[Any]:
    for error in errors:
        yield error
        yield from flatten_errors(error.context)


def error_path(error: Any) -> str:
    return "/".join(str(part) for part in error.absolute_path)


def schema_enum(schemas: dict[str, Any], concept: str) -> set[str]:
    filename, definition, property_name = STATE_SOURCES[concept]
    return set(schemas[filename]["$defs"][definition]["properties"][property_name]["enum"])


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def has_required_not(branch: dict[str, Any], property_name: str) -> bool:
    return branch.get("not") == {"required": [property_name]}


def fixed_source_catalog(instance: dict[str, Any]) -> bool:
    systems = instance.get("systems", [])
    if not isinstance(systems, list) or [system.get("source_system_id") for system in systems] != ["VBQPPL", "VNU", "UEB"]:
        return False
    expected = {
        "VBQPPL": ("ACTIVE", "CORE", 1, "NOT_IMPLEMENTED", "SOAP_ASMX", VBQPPL_ENDPOINT),
        "VNU": ("PLANNED", "LATER", 2, "NOT_IMPLEMENTED", "NOT_CONFIGURED", None),
        "UEB": ("PLANNED", "LATER", 3, "NOT_IMPLEMENTED", "NOT_CONFIGURED", None),
    }
    for system in systems:
        status, phase, priority, implementation, transport, endpoint = expected[system["source_system_id"]]
        policy = system.get("operation_policy", {})
        if (system.get("lifecycle_status"), system.get("rollout_phase"), system.get("rollout_priority"), system.get("connector_implementation_status"), system.get("transport_profile"), system.get("endpoint_url")) != (status, phase, priority, implementation, transport, endpoint):
            return False
        if policy.get("access_mode") != "READ_ONLY" or policy.get("enforcement") != "DENY_BY_DEFAULT" or policy.get("operation_allowlist_status") != "PENDING_VERIFICATION" or policy.get("allowed_operations") != [] or set(policy.get("denied_operation_classes", [])) != {"CREATE", "UPDATE", "REMOVE", "DELETE", "WRITE"}:
            return False
    return True


SOURCE_SEMANTIC_CHECKS = {"fixed_source_catalog": fixed_source_catalog}


def main() -> int:
    print(f"jsonschema={importlib.metadata.version('jsonschema')}")
    print(f"referencing={importlib.metadata.version('referencing')}")
    errors: list[str] = []
    schemas: dict[str, Any] = {}
    for name in SCHEMA_NAMES:
        try:
            schemas[name] = load_json(SCHEMAS / name)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"schema load {name}: {exc}")

    schema_ids: list[str] = []
    for name, schema in schemas.items():
        schema_id = schema.get("$id") if isinstance(schema, dict) else None
        valid_id = isinstance(schema_id, str) and schema_id.startswith(NAMESPACE)
        valid_id = valid_id and urlparse(schema_id).scheme == "https" and not urlparse(schema_id).fragment
        add_error(errors, schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name}: missing Draft 2020-12 $schema")
        add_error(errors, valid_id, f"{name}: invalid schema $id")
        add_error(errors, isinstance(schema.get("title"), str), f"{name}: missing title")
        add_error(errors, isinstance(schema.get("description"), str), f"{name}: missing description")
        add_error(errors, isinstance(schema.get("x-owner"), str), f"{name}: missing x-owner")
        if valid_id and isinstance(schema_id, str):
            schema_ids.append(schema_id)
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"{name}: invalid metaschema: {exc}")
    add_error(errors, len(schemas) == len(SCHEMA_NAMES), "must load exactly 14 schemas")
    add_error(errors, len(schema_ids) == len(set(schema_ids)), "schema $ids are not unique")

    registry = Registry()
    if len(schema_ids) == len(schemas):
        registry = registry.with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    refs_checked = 0
    ref_fragments_resolved = 0
    resource_ids = set(schema_ids)
    for name, schema in schemas.items():
        base_id = schema.get("$id", "")
        resolver = registry.resolver(base_uri=base_id)
        for ref in walk_refs(schema):
            refs_checked += 1
            resolved = urljoin(base_id, ref)
            resource, fragment = urldefrag(resolved)
            add_error(errors, resource in resource_ids, f"{name}: unresolved offline $ref base {ref}")
            try:
                resolver.lookup(ref)
                if fragment:
                    ref_fragments_resolved += 1
            except (Unresolvable, PointerToNowhere, Exception) as exc:
                errors.append(f"{name}: unresolved offline $ref {ref}: {exc}")

    broken_ref_self_test = False
    try:
        test_id = "https://schemas.example.invalid/legal-chatbot/v1/validator-self-test.schema.json"
        test_registry = Registry().with_resource(test_id, Resource.from_contents({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": test_id, "$defs": {}}))
        test_registry.resolver(base_uri=test_id).lookup("#/$defs/missing")
    except (Unresolvable, PointerToNowhere, Exception):
        broken_ref_self_test = True
    add_error(errors, broken_ref_self_test, "broken $ref self-test did not reject missing fragment")

    format_checker = FormatChecker()
    catalog: Any = {}
    try:
        catalog = load_json(CATALOG)
        catalog_validator = Draft202012Validator({"$ref": schemas["state-machine.schema.json"]["$id"] + "#/$defs/Catalog"}, registry=registry, format_checker=format_checker)
        for error in sorted(catalog_validator.iter_errors(catalog), key=lambda item: list(item.absolute_path)):
            errors.append(f"catalog schema {list(error.absolute_path)}: {error.message}")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        errors.append(f"catalog load/validation: {exc}")

    machines = catalog.get("machines", []) if isinstance(catalog, dict) else []
    concepts = [machine.get("concept") for machine in machines if isinstance(machine, dict)]
    add_error(errors, len(machines) == 16, "catalog must have exactly 16 machines")
    add_error(errors, set(concepts) == set(EXPECTED_CONCEPTS) and len(concepts) == len(set(concepts)), "catalog concepts must occur exactly once")
    state_count = 0
    transition_count = 0
    for machine in machines:
        if not isinstance(machine, dict):
            continue
        concept = machine.get("concept", "")
        states = machine.get("states", [])
        initial = machine.get("initial_states", [])
        terminal = machine.get("terminal_states", [])
        transitions = machine.get("transitions", [])
        state_count += len(states)
        transition_count += len(transitions)
        add_error(errors, len(states) == len(set(states)), f"{concept}: duplicate states")
        add_error(errors, set(initial).issubset(states), f"{concept}: initial state outside state set")
        add_error(errors, set(terminal).issubset(states), f"{concept}: terminal state outside state set")
        edges = [(edge.get("from"), edge.get("to")) for edge in transitions if isinstance(edge, dict)]
        add_error(errors, len(edges) == len(set(edges)), f"{concept}: duplicate edges")
        for source, target in edges:
            add_error(errors, source in states and target in states, f"{concept}: edge endpoint outside state set")
            add_error(errors, source not in terminal, f"{concept}: terminal state has outgoing edge")
        if concept in STATE_SOURCES:
            add_error(errors, set(states) == schema_enum(schemas, concept), f"{concept}: catalog states do not match schema enum")

    manifest = load_json(EXAMPLES / "manifest.json")
    fixtures = manifest.get("fixtures", [])
    declared_paths = {fixture.get("path") for fixture in fixtures if isinstance(fixture, dict)}
    actual_paths = {path.relative_to(EXAMPLES).as_posix() for path in EXAMPLES.rglob("*.json") if path.name != "manifest.json"}
    add_error(errors, declared_paths == actual_paths and len(declared_paths) == len(fixtures), "manifest fixture paths must exactly match fixture files")
    valid_fixture_count = 0
    invalid_fixture_count = 0
    for fixture in fixtures:
        instance = load_json(EXAMPLES / fixture["path"])
        schema = schemas[fixture["schema"]]
        validator = Draft202012Validator({"$ref": schema["$id"] + "#/$defs/" + fixture["definition"]}, registry=registry, format_checker=format_checker)
        fixture_errors = list(flatten_errors(validator.iter_errors(instance)))
        expected = fixture["expected"]
        add_error(errors, expected in {"VALID", "INVALID"}, f"fixture {fixture['path']} has unsupported expected value {expected}")
        semantic_name = fixture.get("semantic_check")
        if semantic_name is not None:
            add_error(errors, semantic_name in SOURCE_SEMANTIC_CHECKS, f"fixture {fixture['path']} has unknown semantic check {semantic_name}")
        semantic_result = SOURCE_SEMANTIC_CHECKS[semantic_name](instance) if semantic_name in SOURCE_SEMANTIC_CHECKS else semantic_name is None
        if expected == "VALID":
            valid_fixture_count += 1
            add_error(errors, not fixture_errors, f"fixture {fixture['path']} expected VALID")
            add_error(errors, semantic_result, f"fixture {fixture['path']} failed semantic check {semantic_name}")
        else:
            invalid_fixture_count += 1
            add_error(errors, bool(fixture_errors), f"fixture {fixture['path']} expected INVALID")
            keyword = fixture.get("error_keyword")
            expected_path = fixture.get("error_path")
            if keyword:
                matches = [error for error in fixture_errors if error.validator == keyword]
                add_error(errors, bool(matches), f"fixture {fixture['path']} lacks expected keyword {keyword}")
                if expected_path is not None:
                    add_error(errors, any(error_path(error) == expected_path for error in matches), f"fixture {fixture['path']} lacks expected {keyword} path {expected_path}")

    provider = schemas["provider-config-view.schema.json"]["$defs"]["ProviderConfigView"]
    provider_keys = [key.lower() for key in walk_property_keys(provider)]
    grounded = schemas["chat.schema.json"]["$defs"]["GroundedAnswer"]
    grounded_branches = grounded["oneOf"]
    citation = schemas["citation.schema.json"]["$defs"]["Citation"]
    citation_valid, citation_nonvalid = citation["oneOf"]
    golden = schemas["feedback.schema.json"]["$defs"]["GoldenAnswer"]
    golden_then = golden["allOf"][0]["then"]
    dataset = schemas["evaluation.schema.json"]["$defs"]["Dataset"]
    dataset_then = dataset["allOf"][0]["then"]
    retrieval = schemas["retrieval.schema.json"]["$defs"]["RetrievalRun"]
    sufficient_then, insufficient_then = (rule["then"] for rule in retrieval["allOf"])
    claim = schemas["chat.schema.json"]["$defs"]["GroundedClaim"]
    candidate = schemas["evaluation.schema.json"]["$defs"]["Candidate"]
    source_schema = schemas["source-connector-port.schema.json"]
    source_defs = source_schema["$defs"]
    source_port_definitions = [
        source_defs[name] for name in (
            "SourceSystem", "SourceDocumentRef", "SourceDiscoveryRequest",
            "SourceDiscoveryPage", "SourceFetchRequest", "FetchedSourceDocument",
        )
    ]
    source_fixture_paths = [fixture["path"] for fixture in fixtures if "source-" in fixture["path"]]
    source_fixture_keys = [key.lower() for path in source_fixture_paths for key in walk_instance_keys(load_json(EXAMPLES / path))]
    source_fixture_instances = [load_json(EXAMPLES / path) for path in source_fixture_paths]
    source_port_keys = [key.lower() for definition in source_port_definitions for key in walk_property_keys(definition)]
    source_system_branches = source_defs["SourceSystem"].get("oneOf", [])
    planned_fixture_urls_absent = all(
        "endpoint_url" not in instance and "source_document_url" not in instance and instance.get("transport_profile") != "SOAP_ASMX" and instance.get("connector_implementation_status") != "IMPLEMENTED"
        for instance in source_fixture_instances
        if isinstance(instance, dict) and instance.get("source_system_id") in {"VNU", "UEB"}
    )
    provider_machine = next((machine for machine in machines if machine.get("concept") == "ProviderConfigView"), {})
    provider_invariants = provider_machine.get("invariants", [])
    representation_invariant = next((invariant for invariant in provider_invariants if invariant.get("enforcement") == "HUMAN_GATE"), {})
    source_system_validator = Draft202012Validator({"$ref": source_schema["$id"] + "#/$defs/SourceSystem"}, registry=registry, format_checker=format_checker)
    source_ref_validator = Draft202012Validator({"$ref": source_schema["$id"] + "#/$defs/SourceDocumentRef"}, registry=registry, format_checker=format_checker)
    policy = {"access_mode": "READ_ONLY", "enforcement": "DENY_BY_DEFAULT", "operation_allowlist_status": "PENDING_VERIFICATION", "allowed_operations": [], "denied_operation_classes": ["CREATE", "UPDATE", "REMOVE", "DELETE", "WRITE"]}
    lifecycle_instances = []
    for lifecycle_status in ("ACTIVE", "PLANNED", "DISABLED", "RETIRED"):
        instance = {"source_system_id": "VBQPPL", "display_name": "Synthetic lifecycle validation", "lifecycle_status": lifecycle_status, "rollout_priority": 1, "connector_implementation_status": "NOT_IMPLEMENTED", "operation_policy": policy, "description": "In-memory schema reachability check."}
        if lifecycle_status == "ACTIVE":
            instance.update({"rollout_phase": "CORE", "transport_profile": "SOAP_ASMX", "endpoint_url": VBQPPL_ENDPOINT})
        else:
            instance.update({"rollout_phase": "LATER", "transport_profile": "NOT_CONFIGURED"})
        lifecycle_instances.append(instance)
    reachable_states = {instance["lifecycle_status"] for instance in lifecycle_instances if not list(source_system_validator.iter_errors(instance))}
    source_machine = next((machine for machine in machines if machine.get("concept") == "SourceSystem"), {})
    source_edges_reachable = all(edge.get("from") in reachable_states and edge.get("to") in reachable_states for edge in source_machine.get("transitions", []))
    registry_endpoint_ref = {"source_system_id": "VBQPPL", "source_external_id": "vbqppl-synthetic-001", "source_document_url": VBQPPL_ENDPOINT, "source_updated_at": "2026-08-13T00:00:00Z", "fetched_at": "2026-08-13T00:01:00Z", "raw_payload_hash": "sha256:vbqppl-synthetic-0001", "mapping_version": "vbqppl-map-v1"}
    registry_endpoint_errors = list(flatten_errors(source_ref_validator.iter_errors(registry_endpoint_ref)))
    catalog_systems_schema = source_defs["SourceSystemCatalog"]["properties"]["systems"]
    security_checks = {
        "provider_no_forbidden_keys": not [key for key in provider_keys if any(token in key for token in FORBIDDEN_PROVIDER_KEYS)],
        "grounded_answer_metadata_excluded": not [item for item in [key.lower() for key in walk_property_keys(grounded)] + [ref.lower() for ref in walk_refs(grounded)] if any(token in item for token in FORBIDDEN_GROUNDED_TOKENS)],
        "grounded_answer_exclusive_branches": has_required_not(grounded_branches[0], "refusal") and has_required_not(grounded_branches[1], "claims"),
        "grounded_claim_requires_chunk_ids": "chunk_ids" in claim.get("required", []) and claim["properties"]["chunk_ids"].get("minItems") == 1,
        "citation_exclusive_authority": has_required_not(citation_valid, "reason_codes") and citation_nonvalid.get("not", {}).get("anyOf") == [{"required": ["document_id"]}, {"required": ["version_id"]}, {"required": ["chunk_ids"]}, {"required": ["canonical_source"]}],
        "golden_approved_requires_human_citations": set(("approved_by", "approved_at", "citation_validation_ids")).issubset(golden_then.get("required", [])),
        "dataset_frozen_requires_manifest_time_members": set(("manifest_hash", "frozen_at")).issubset(dataset_then.get("required", [])) and dataset_then["properties"]["members"].get("minItems") == 1,
        "retrieval_outcomes_exclusive": has_required_not(sufficient_then, "refusal") and set(("refusal", "completed_at")).issubset(insufficient_then.get("required", [])),
        "candidate_no_activation": not set(candidate["properties"]["status"]["enum"]).intersection({"ACTIVE", "DEPLOYED", "RELEASED"}) and not any("activation" in key.lower() or "release" in key.lower() for key in walk_property_keys(candidate)),
        "representation_not_activation": "ACTIVE" in provider["properties"]["status"]["enum"] and representation_invariant.get("enforcement") == "HUMAN_GATE" and all(term in representation_invariant.get("description", "").lower() for term in ("later", "separate", "rollback")) and ("single" in representation_invariant.get("description", "").lower() or "one answer provider" in representation_invariant.get("description", "").lower()),
        "fake_provider_key_is_null": load_json(EXAMPLES / "invalid/provider-config-with-api-key.json").get("api_key") is None,
        "source_property_keys_exclude_sensitive_material": not [key for key in source_port_keys + source_fixture_keys if any(token in key for token in FORBIDDEN_SOURCE_KEYS)],
        "source_catalog_fixed_governance": fixed_source_catalog(load_json(EXAMPLES / "success/source-system-catalog.json")),
        "source_catalog_structural_exact": catalog_systems_schema.get("minItems") == 3 and catalog_systems_schema.get("maxItems") == 3 and catalog_systems_schema.get("items") is False and [item.get("$ref") for item in catalog_systems_schema.get("prefixItems", [])] == ["#/$defs/VBQPPLCurrent", "#/$defs/VNUCurrent", "#/$defs/UEBCurrent"],
        "source_lifecycle_states_schema_reachable": reachable_states == {"ACTIVE", "PLANNED", "DISABLED", "RETIRED"} and source_edges_reachable,
        "source_connector_not_implemented": all(system.get("connector_implementation_status") == "NOT_IMPLEMENTED" for system in load_json(EXAMPLES / "success/source-system-catalog.json")["systems"]),
        "source_operation_allowlist_empty_pending": all(system["operation_policy"].get("operation_allowlist_status") == "PENDING_VERIFICATION" and system["operation_policy"].get("allowed_operations") == [] for system in load_json(EXAMPLES / "success/source-system-catalog.json")["systems"]),
        "source_port_active_id_only": source_defs["ActiveSourceSystemId"].get("const") == "VBQPPL" and all(source_defs[name]["properties"]["source_system_id"].get("$ref") == "#/$defs/ActiveSourceSystemId" for name in ("SourceDocumentRef", "SourceDiscoveryRequest", "SourceDiscoveryPage", "SourceFetchRequest")) and source_defs["FetchedSourceDocument"]["properties"]["source_ref"].get("$ref") == "#/$defs/SourceDocumentRef",
        "source_ref_required_fields_declared": set(("source_system_id", "source_external_id", "source_document_url", "source_updated_at", "fetched_at", "raw_payload_hash", "mapping_version")).issubset(source_defs["SourceDocumentRef"].get("required", [])),
        "source_ref_url_https_vbqppl_pattern": source_defs["SourceDocumentRef"]["properties"]["source_document_url"].get("format") == "uri" and source_defs["SourceDocumentRef"]["properties"]["source_document_url"].get("pattern") == "^https://ws\\.vbpl\\.vn(?:/|$)",
        "source_ref_rejects_registry_endpoint": any(error.validator == "not" for error in registry_endpoint_errors),
        "source_version_origin_exclusive": "ingestion_origin" in schemas["document.schema.json"]["$defs"]["Version"].get("required", []) and len(schemas["document.schema.json"]["$defs"]["Version"].get("allOf", [])) == 2,
        "source_port_dtos_exclude_endpoint_operation": not any(key in {"endpoint_url", "allowed_operations", "operation", "operation_name"} for definition in source_port_definitions[2:] for key in walk_property_keys(definition)),
        "source_sensitive_key_self_test": "credential" in set(walk_instance_keys({"nested": {"credential": None}})),
        "planned_sources_have_no_url_fixture": planned_fixture_urls_absent,
        "rollout_not_legal_authority": "legal" in source_defs["SourceSystem"].get("description", "").lower() and "ranking" in source_defs["SourceSystem"]["properties"]["rollout_priority"].get("description", "").lower(),
        "fixture_expected_values_strict": all(fixture.get("expected") in {"VALID", "INVALID"} for fixture in fixtures),
    }
    for check_name, passed in security_checks.items():
        add_error(errors, passed, f"security/invariant check failed: {check_name}")

    summary = {
        "broken_ref_self_test": broken_ref_self_test,
        "errors": errors,
        "invalid_fixture_count": invalid_fixture_count,
        "ref_fragments_resolved": ref_fragments_resolved,
        "refs_checked": refs_checked,
        "schema_count": len(schemas),
        "schema_ids": sorted(schema_ids),
        "security_checks": security_checks,
        "state_count": state_count,
        "state_machine_count": len(machines),
        "transition_count": transition_count,
        "valid_fixture_count": valid_fixture_count,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
