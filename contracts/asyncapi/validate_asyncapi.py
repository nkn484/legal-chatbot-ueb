"""Offline bounded linter for the Prompt 02.5 AsyncAPI catalog.

This is deliberately not an official AsyncAPI parser or CLI.  It validates the
approved catalog subset and uses only stdlib plus environment-provided PyYAML,
jsonschema, and referencing.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parent
CONTRACTS_ROOT = ROOT.parent
ERRORS: list[str] = []
INDEX_EVENT_STATUS = {
    "legal.index.projection.ready.v1": "READY",
    "legal.index.projection.activated.v1": "ACTIVE",
    "legal.index.projection.failed.v1": "FAILED",
    "legal.index.projection.retired.v1": "RETIRED",
}
PLANNED_CONSUMERS = {
    "legal.document.source.invalidated.v1": ["feedback-service", "evaluation-service"],
    "legal.document.source.revoked.v1": ["feedback-service", "evaluation-service"],
    "legal.chat.answer.snapshot.available.v1": ["feedback-service"],
    "legal.golden.answer.approved.v1": ["evaluation-service"],
    "legal.golden.answer.revoked.v1": ["evaluation-service"],
}


class StrictLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects aliases, merges, duplicate, and non-string keys."""


def _mapping(loader: StrictLoader, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key_node, value_node in node.value:
        if not isinstance(key_node, yaml.ScalarNode) or not isinstance(key_node.value, str):
            raise yaml.YAMLError("mapping key must be a string scalar")
        key = key_node.value
        if key == "<<":
            raise yaml.YAMLError("YAML merge keys are forbidden")
        if key in output:
            raise yaml.YAMLError(f"duplicate YAML key: {key}")
        output[key] = loader.construct_object(value_node, deep=deep)
    return output


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def fail(message: str) -> None:
    ERRORS.append(message)


def yaml_load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    for token in yaml.scan(text):
        if isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken)):
            raise yaml.YAMLError(f"YAML anchors and aliases are forbidden in {path}")
    nodes = list(yaml.compose_all(text))
    for node in nodes:
        def visit(value: yaml.Node) -> None:
            if getattr(value, "anchor", None):
                raise yaml.YAMLError(f"anchors are forbidden in {path}")
            if isinstance(value, yaml.MappingNode):
                for k, v in value.value:
                    visit(k); visit(v)
            elif isinstance(value, yaml.SequenceNode):
                for child in value.value:
                    visit(child)
        if node is not None:
            visit(node)
    return yaml.load(text, Loader=StrictLoader)


def json_load(path: Path) -> Any:
    def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_keys)


def fragment(document: Any, pointer: str) -> Any:
    current = document
    if not pointer:
        return current
    for token in pointer.lstrip("/").split("/"):
        current = current[token.replace("~1", "/").replace("~0", "~")]
    return current


def local_ref_ok(ref: str, current: Path, docs: dict[Path, Any]) -> bool:
    target, pointer = urldefrag(ref)
    if target.startswith(("http://", "https://", "file:")):
        fail(f"network or absolute ref forbidden: {ref}")
        return False
    path = current if not target else (current.parent / target).resolve()
    try:
        path.relative_to(CONTRACTS_ROOT.resolve())
    except ValueError:
        fail(f"ref escapes contracts/: {ref}")
        return False
    if path not in docs:
        fail(f"missing local ref target: {ref}")
        return False
    try:
        fragment(docs[path], pointer)
    except (KeyError, TypeError):
        fail(f"unresolved ref fragment: {ref}")
        return False
    return True


def walk_refs(value: Any, current: Path, docs: dict[Path, Any]) -> int:
    count = 0
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                count += 1
                local_ref_ok(child, current, docs)
            count += walk_refs(child, current, docs)
    elif isinstance(value, list):
        for child in value:
            count += walk_refs(child, current, docs)
    return count


def const_value(schema: dict[str, Any], field: str) -> Any:
    for part in schema.get("allOf", []):
        if isinstance(part, dict) and field in part.get("properties", {}):
            return part["properties"][field].get("const")
    return None


def component_schema(component: dict[str, Any], docs: dict[Path, Any]) -> dict[str, Any]:
    ref = component["payload"]["$ref"]
    source, pointer = urldefrag(ref)
    document = docs[(ROOT / source).resolve()]
    return {"$ref": f"{document['$id']}#{pointer}"}


def concrete_component_schema(component: dict[str, Any], docs: dict[Path, Any]) -> dict[str, Any]:
    """Resolve a component's local schema alias for catalog constant inspection."""
    source, pointer = urldefrag(component["payload"]["$ref"])
    path = (ROOT / source).resolve()
    value = fragment(docs[path], pointer)
    while isinstance(value, dict) and "$ref" in value:
        target, target_pointer = urldefrag(value["$ref"])
        path = path if not target else (path.parent / target).resolve()
        value = fragment(docs[path], target_pointer)
    return value


def property_scan(value: Any, deny: set[str], allowed: set[str], label: str) -> None:
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            for name in properties:
                check_key(name, deny, allowed, label)
        for key, child in value.items():
            if key != "properties":
                property_scan(child, deny, allowed, label)
    elif isinstance(value, list):
        for child in value:
            property_scan(child, deny, allowed, label)


def check_key(key: str, deny: set[str], allowed: set[str], label: str) -> None:
    lowered = key.lower()
    if lowered in allowed:
        return
    if any(token in lowered for token in deny):
        fail(f"forbidden property key {key!r} in {label}")


def canonical_json(value: Any) -> str:
    """Project canonical JSON for payload_hash; intentionally not RFC JCS."""
    def validate(node: Any) -> None:
        if node is None or isinstance(node, (str, bool, int)):
            return
        if isinstance(node, float):
            raise ValueError("floats are forbidden in canonical event data")
        if isinstance(node, list):
            for child in node:
                validate(child)
            return
        if isinstance(node, dict) and all(isinstance(key, str) for key in node):
            for child in node.values():
                validate(child)
            return
        raise ValueError("data must contain JSON strings/integers/booleans/null, arrays, or objects")
    validate(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_digest(data: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def all_property_schemas(value: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        if isinstance(value.get("properties"), dict):
            found.extend(value["properties"].items())
        for child in value.values():
            found.extend(all_property_schemas(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(all_property_schemas(child))
    return found


def hash_schema_ok(schema: Any) -> bool:
    if not isinstance(schema, dict):
        return False
    return schema.get("$ref") == "common.schema.json#/$defs/HashValue" or schema.get("pattern") == "^sha256:[0-9a-f]{64}$"


def ownership_model_ok(spec: dict[str, Any], inventory: dict[str, Any], audit_producers: list[str]) -> bool:
    """Pure ownership/ACL check also used by mutation probes."""
    components = spec.get("components", {}).get("messages", {})
    channels = spec.get("channels", {})
    operations = spec.get("operations", {})
    operations_by_component: dict[str, list[dict[str, Any]]] = {name: [] for name in components}
    for operation in operations.values():
        channel_ref = str(operation.get("channel", {}).get("$ref", ""))
        channel = channels.get(str(channel_ref).rsplit("/", 1)[-1], {})
        channel_refs = {entry.get("$ref") for entry in channel.get("messages", {}).values() if isinstance(entry, dict)}
        for item in operation.get("messages", []):
            ref = str(item.get("$ref", ""))
            if ref.startswith("#/components/messages/"):
                if ref not in channel_refs:
                    return False
                operations_by_component.setdefault(ref.rsplit("/", 1)[-1], []).append(operation)
    for message_type, item in inventory.items():
        component = item["component"]
        ops = operations_by_component.get(component, [])
        if item["activation"] == "LATER":
            if ops:
                return False
            continue
        sends = [op for op in ops if op.get("action") == "send"]
        receives = [op for op in ops if op.get("action") == "receive"]
        if len(sends) != 1 or len(receives) != len(item["consumers"]):
            return False
        channel_ref = sends[0].get("channel", {}).get("$ref", "")
        if not channel_ref.startswith("#/channels/"):
            return False
        channel = channels.get(channel_ref.rsplit("/", 1)[-1], {})
        exchange = channel.get("bindings", {}).get("amqp", {}).get("exchange", {}).get("name")
        if exchange != ("legal.commands" if item["kind"] == "COMMAND" else "legal.events"):
            return False
        if item["kind"] == "COMMAND":
            if channel.get("x-ueb-directed-consumer") != "processing-service" or item["consumers"] != ["processing-service"]:
                return False
        if {op.get("x-ueb-consumer-service") for op in receives} != set(item["consumers"]):
            return False
        acl = components[component].get("x-ueb-acl", {})
        expected_publish = audit_producers if item["producer"] == "MULTI_PRODUCER_EXCEPTION" else [item["producer"]]
        if acl.get("publish") != expected_publish or acl.get("consume") != item["consumers"]:
            return False
        if item["producer"] == "MULTI_PRODUCER_EXCEPTION":
            if sends[0].get("x-ueb-producer-services") != audit_producers or "audit-service" in audit_producers:
                return False
        elif sends[0].get("x-ueb-producer-service") != item["producer"]:
            return False
    return True


def run_scenario_checks(valid_payloads: dict[str, dict[str, Any]], policy: dict[str, Any], spec: dict[str, Any], inventory: dict[str, Any], audit_producers: list[str]) -> dict[str, bool]:
    """Deterministic state probes backing delivery-scenarios.yaml, never labels alone."""
    published = copy.deepcopy(valid_payloads["legal.document.published.v1"])
    artifacts = copy.deepcopy(valid_payloads["legal.processing.artifacts.ready.v1"])
    request = copy.deepcopy(valid_payloads["legal.document.version.processing.requested.v1"])
    candidate = copy.deepcopy(valid_payloads["legal.candidate.eligible.v1"])
    inbox: dict[str, str] = {}
    def receive(message: dict[str, Any]) -> str:
        prior = inbox.get(message["message_id"])
        if prior is None:
            inbox[message["message_id"]] = message["payload_hash"]
            return "applied"
        return "no_op" if prior == message["payload_hash"] else "integrity_reject"
    first = receive(published); duplicate = receive(copy.deepcopy(published))
    altered = copy.deepcopy(published); altered["data"]["effect_hash"] = "sha256:" + "a" * 64; altered["payload_hash"] = payload_digest(altered["data"])
    state = {"highest": 2, "published": True}
    stale = "no_op" if 1 < state["highest"] else "applied"
    gap = "reconcile" if 4 > state["highest"] + 1 else "applied"
    state = {"highest": 3, "published": False}
    delayed_publish = {"aggregate_revision": 2}
    unpublish_result = "no_op" if delayed_publish["aggregate_revision"] < state["highest"] and not state["published"] else "applied"
    artifact_matches = all(artifacts["data"][key] == request["data"][key] for key in ("document_id", "version_id", "version_revision", "input_hash"))
    artifacts_bad = copy.deepcopy(artifacts); artifacts_bad["data"]["input_hash"] = "sha256:" + "b" * 64
    mutations = copy.deepcopy(spec)
    mutations["operations"]["jobSucceededSend"]["x-ueb-producer-service"] = "chat-service"
    later_mutation = copy.deepcopy(spec)
    later_mutation["operations"]["laterInjected"] = {"action": "send", "channel": {"$ref": "#/channels/documentPublished"}, "messages": [{"$ref": "#/components/messages/CandidateEligible"}]}
    allowed_actions = {"recommendation_code", "candidate_id", "candidate_revision", "evaluation_id", "evaluation_revision", "result_hash"}
    source_live = False
    activation = "refused" if not source_live else "applied"
    unknown = copy.deepcopy(valid_payloads["legal.processing.job.succeeded.v1"])
    unknown["message_type"] = "legal.processing.job.succeeded.v2"
    feedback_effect = {"golden_created": False, "dataset_created": False}
    golden_without_evidence = {"golden_answer_id": "gld-0001", "golden_revision": 1}
    frozen_members = {"gld-0001"}
    revoked_members = {"gld-0001"}
    provider_allowed = {"configuration_id", "configuration_revision", "configuration_hash", "validation_code"}
    document_allowed = {"document_id", "document_revision", "version_id", "version_revision", "content_hash", "metadata_hash", "effect_hash"}
    return {
        "duplicate_same_hash": first == "applied" and duplicate == "no_op",
        "duplicate_changed_hash": receive(altered) == "integrity_reject",
        "stale_revision": stale == "no_op",
        "revision_gap": gap == "reconcile",
        "unpublish_dominates": unpublish_result == "no_op",
        "revoked_activation_refused": activation == "refused",
        "artifacts_relation_mismatch": artifact_matches and artifacts_bad["data"]["input_hash"] != request["data"]["input_hash"],
        "unknown_type_rejected": unknown["message_type"] not in inventory and not unknown["message_type"].endswith(".v1"),
        "unauthorized_producer_rejected": not ownership_model_ok(mutations, inventory, audit_producers),
        "permanent_direct_dlq": policy["retry"]["permanent_action"] == "DLQ_IMMEDIATELY",
        "transient_retry_schedule": policy["retry"]["max_deliveries_including_initial"] == 5 and policy["retry"]["delays_seconds"] == [30, 120, 600, 1800],
        "replay_duplicate_noop": duplicate == "no_op" and published["message_id"] == copy.deepcopy(published)["message_id"],
        "audit_terminal": "audit-service" not in audit_producers,
        "feedback_no_ground_truth": not feedback_effect["golden_created"] and not feedback_effect["dataset_created"],
        "golden_evidence_required": not {"approval_snapshot_id", "citation_validation_ids"} <= set(golden_without_evidence),
        "revocation_tombstone": bool(frozen_members & revoked_members),
        "candidate_recommendation_only": set(candidate["data"]) <= allowed_actions and candidate["data"]["recommendation_code"] == "ELIGIBLE_FOR_HUMAN_REVIEW",
        "provider_secret_rejected": "secret" not in provider_allowed and "endpoint" not in provider_allowed,
        "forbidden_text_rejected": "full_text" not in document_allowed and "storage_key" not in document_allowed,
        "later_injection_rejected": not ownership_model_ok(later_mutation, inventory, audit_producers),
    }


def delivery_errors(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("delivery") != "AT_LEAST_ONCE" or policy.get("exactly_once") is not False:
        errors.append("delivery/exactly_once")
    if policy.get("retry", {}).get("max_deliveries_including_initial") != 5:
        errors.append("max deliveries")
    if policy.get("retry", {}).get("delays_seconds") != [30, 120, 600, 1800]:
        errors.append("retry delays")
    if policy.get("dlq", {}).get("automatic_replay") is not False:
        errors.append("automatic replay")
    if policy.get("ordering", {}).get("scope") != "aggregate_metadata_only":
        errors.append("ordering scope")
    if policy.get("retention", {}).get("main_retry_max_days") != 7 or policy.get("retention", {}).get("dlq_max_days") != 14:
        errors.append("retention")
    if not policy.get("dlq") or not policy.get("retry"):
        errors.append("missing DLQ/retry")
    return errors


def output_path(value: str | None) -> Path | None:
    if value is None:
        return None
    target = Path(value).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("--output must be under contracts/asyncapi/") from exc
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline bounded AsyncAPI contract validator")
    parser.add_argument("--output", help="repo-relative or absolute report path under contracts/asyncapi/")
    args = parser.parse_args()
    try:
        report_path = output_path(args.output)
    except ValueError as exc:
        print(json.dumps({"errors": [str(exc)]}, sort_keys=True))
        return 2
    spec_path = ROOT / "asyncapi.yaml"
    config_path = ROOT / "lint-config.yaml"
    policy_path = ROOT / "delivery-policy.yaml"
    scenarios_path = ROOT / "delivery-scenarios.yaml"
    manifest_path = ROOT / "examples" / "manifest.yaml"
    try:
        spec = yaml_load(spec_path)
        config = yaml_load(config_path)
        policy = yaml_load(policy_path)
        scenarios = yaml_load(scenarios_path)
        manifest = yaml_load(manifest_path)
        schema_paths = sorted((ROOT / "schemas").glob("*.json"))
        docs: dict[Path, Any] = {path.resolve(): json_load(path) for path in schema_paths}
        docs[spec_path.resolve()] = spec
    except Exception as exc:  # parse errors are deterministic lint errors
        fail(f"parse failure: {exc}")
        print(json.dumps({"errors": ERRORS}, sort_keys=True))
        return 1

    if spec.get("asyncapi") != "3.0.0" or spec.get("info", {}).get("version") != "1.0.0" or spec.get("defaultContentType") != "application/json":
        fail("AsyncAPI version, info version, or default content type is wrong")
    if "servers" in spec:
        fail("servers/broker host configuration is forbidden")

    refs = sum(walk_refs(doc, path, docs) for path, doc in docs.items())
    for path, schema in ((p, docs[p.resolve()]) for p in schema_paths):
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            fail(f"invalid JSON Schema {path.name}: {exc}")

    components = spec.get("components", {}).get("messages", {})
    inventory = config.get("messages", {})
    if set(components) != {item["component"] for item in inventory.values()} or len(inventory) != 30:
        fail("components do not exactly match the 30-message inventory")
    channels = spec.get("channels", {})
    operations = spec.get("operations", {})
    by_component: dict[str, list[tuple[str, dict[str, Any]]]] = {name: [] for name in components}
    for operation_id, operation in operations.items():
        if operation.get("action") not in {"send", "receive"}:
            fail(f"invalid operation action: {operation_id}")
        if operation.get("bindings", {}).get("amqp", {}).get("bindingVersion") != "0.3.0":
            fail(f"operation AMQP binding version: {operation_id}")
        channel_ref = operation.get("channel", {}).get("$ref", "")
        if not channel_ref.startswith("#/channels/") or channel_ref.rsplit("/", 1)[-1] not in channels:
            fail(f"invalid operation channel: {operation_id}")
        for message in operation.get("messages", []):
            ref = str(message.get("$ref", ""))
            if not ref.startswith("#/components/messages/"):
                fail(f"invalid operation message ref: {operation_id}")
                continue
            component = ref.rsplit("/", 1)[-1]
            channel = channels[channel_ref.rsplit("/", 1)[-1]]
            declared_refs = {declared.get("$ref") for declared in channel.get("messages", {}).values() if isinstance(declared, dict)}
            if ref not in declared_refs:
                fail(f"operation message is absent from its channel: {operation_id}")
            by_component.setdefault(component, []).append((operation_id, operation))
    for channel_id, channel in channels.items():
        amqp = channel.get("bindings", {}).get("amqp", {})
        exchange = amqp.get("exchange", {})
        if amqp.get("bindingVersion") != "0.3.0" or amqp.get("is") != "routingKey" or exchange.get("type") != "topic" or exchange.get("durable") is not True:
            fail(f"channel AMQP binding: {channel_id}")
        if any(token in json.dumps(channel).lower() for token in ("queue", "vhost", "credential", "quorum")):
            fail(f"forbidden broker topology claim: {channel_id}")
        address = channel.get("address")
        catalog_item = inventory.get(address)
        declared_messages = channel.get("messages")
        if not catalog_item or not isinstance(declared_messages, dict) or len(declared_messages) != 1:
            fail(f"channel address/message mapping invalid: {channel_id}")
            continue
        expected_component = catalog_item["component"]
        expected_ref = f"#/components/messages/{expected_component}"
        if declared_messages.get(expected_component, {}).get("$ref") != expected_ref:
            fail(f"channel does not declare exactly matching component: {channel_id}")

    registry = Registry()
    for path in schema_paths:
        try:
            registry = registry.with_resource(docs[path.resolve()]["$id"], Resource.from_contents(docs[path.resolve()]))
        except Exception as exc:
            fail(f"registry error {path.name}: {exc}")
    valid_count = invalid_schema_count = invalid_semantic_count = 0
    valid_payloads: dict[str, dict[str, Any]] = {}
    aggregate_relation_checks = 0
    payload_hash_checks = 0
    index_projection_checks = 0
    for entry in manifest.get("valid", []):
        valid_count += 1
        component = entry["component"]
        payload = json_load(ROOT / entry["file"])
        valid_payloads[payload["message_type"]] = payload
        schema = component_schema(components[component], docs)
        try:
            Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(payload)
        except Exception as exc:
            fail(f"valid fixture {entry['file']} failed: {exc}")
        try:
            if payload["payload_hash"] != payload_digest(payload["data"]):
                fail(f"payload_hash does not match canonical data: {entry['file']}")
            else:
                payload_hash_checks += 1
        except (KeyError, ValueError) as exc:
            fail(f"payload_hash canonicalization failure {entry['file']}: {exc}")
        item = inventory.get(payload["message_type"], {})
        identifier = item.get("aggregate_id_field")
        revision = item.get("aggregate_revision_field")
        if payload.get("aggregate_id") != payload.get("data", {}).get(identifier) or payload.get("aggregate_revision") != payload.get("data", {}).get(revision) or payload.get("ordering_key") != payload.get("aggregate_id"):
            fail(f"aggregate relation mismatch: {entry['file']}")
        else:
            aggregate_relation_checks += 1
        traceparent = payload.get("traceparent")
        if traceparent and (traceparent.split("-")[1] == "0" * 32 or traceparent.split("-")[2] == "0" * 16):
            fail(f"all-zero traceparent identity: {entry['file']}")
        expected_status = INDEX_EVENT_STATUS.get(payload["message_type"])
        if expected_status is not None:
            if payload["data"].get("mode") != "FTS" or payload["data"].get("status") != expected_status or not payload["data"].get("index_scope"):
                fail(f"index mode/status/scope mismatch: {entry['file']}")
            else:
                index_projection_checks += 1
    valid_components = [entry["component"] for entry in manifest.get("valid", [])]
    if len(valid_components) != 30 or set(valid_components) != set(components) or len(set(valid_components)) != 30:
        fail("manifest must contain exactly one valid fixture per component")
    for field, invalid_value in (("mode", "ACTIVE"), ("status", "ACTIVE")):
        mutated = copy.deepcopy(valid_payloads["legal.index.projection.ready.v1"])
        mutated["data"][field] = invalid_value
        schema = component_schema(components["IndexProjectionReady"], docs)
        try:
            Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(mutated)
            fail(f"index {field} mutation unexpectedly schema-valid")
        except Exception:
            index_projection_checks += 1
    for entry in manifest.get("invalid_schema", []):
        invalid_schema_count += 1
        schema = component_schema(components[entry["component"]], docs)
        try:
            Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(json_load(ROOT / entry["file"]))
            fail(f"invalid-schema fixture unexpectedly valid: {entry['file']}")
        except Exception:
            pass
    for entry in manifest.get("invalid_semantic", []):
        invalid_semantic_count += 1
        payload = json_load(ROOT / entry["file"])
        schema = component_schema(components[entry["component"]], docs)
        try:
            Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).validate(payload)
        except Exception as exc:
            fail(f"semantic fixture must remain schema-valid: {entry['file']}: {exc}")
        if entry["check"] not in {"duplicate_altered_hash", "ordering_key_equals_aggregate_id", "stale_revision_no_op", "artifacts_input_hash_match", "later_not_routable"}:
            fail(f"unknown semantic fixture check: {entry['check']}")
        if entry["check"] == "ordering_key_equals_aggregate_id" and payload["ordering_key"] == payload["aggregate_id"]:
            fail("ordering semantic fixture is not invalid")
        if entry["check"] == "duplicate_altered_hash":
            baseline = valid_payloads[payload["message_type"]]
            if payload["message_id"] != baseline["message_id"] or payload["data"] == baseline["data"] or payload["payload_hash"] == baseline["payload_hash"]:
                fail("duplicate mutation fixture is not a same-id changed-data/hash pair")
        if entry["check"] == "stale_revision_no_op" and payload["aggregate_revision"] >= valid_payloads[payload["message_type"]]["aggregate_revision"]:
            fail("stale fixture is not older than stored revision")
        if entry["check"] == "artifacts_input_hash_match" and payload["data"]["input_hash"] == valid_payloads["legal.document.version.processing.requested.v1"]["data"]["input_hash"]:
            fail("artifact mismatch fixture lacks a distinct input hash")
        if entry["check"] == "later_not_routable" and inventory[payload["message_type"]]["routable"]:
            fail("later fixture targets routable catalog entry")

    for message_type, item in inventory.items():
        component = components.get(item["component"])
        if not component:
            continue
        if component.get("contentType") != "application/json" or component.get("bindings", {}).get("amqp", {}).get("bindingVersion") != "0.3.0" or not component.get("x-ueb-example"):
            fail(f"message binding/content/example: {item['component']}")
        schema = concrete_component_schema(component, docs)
        if const_value(schema, "message_type") != message_type or const_value(schema, "message_kind") != item["kind"] or const_value(schema, "aggregate_type") != item["aggregate_type"]:
            fail(f"envelope constants do not match catalog: {message_type}")
        if item["producer"] != "MULTI_PRODUCER_EXCEPTION" and const_value(schema, "producer_service") != item["producer"]:
            fail(f"producer const does not match catalog: {message_type}")
        active_ops = by_component.get(item["component"], [])
        if item["activation"] == "LATER":
            if component.get("x-ueb-activation") != "LATER" or component.get("x-ueb-routable") is not False or active_ops:
                fail(f"LATER component appears routable: {message_type}")
        else:
            sends = [op for _, op in active_ops if op.get("action") == "send"]
            receives = [op for _, op in active_ops if op.get("action") == "receive"]
            if component.get("x-ueb-activation") != "CORE" or component.get("x-ueb-routable") is not True or len(sends) != 1 or len(receives) != len(item["consumers"]):
                fail(f"CORE operation coverage: {message_type}")
            got_consumers = {op.get("x-ueb-service") for op in receives}
            if got_consumers != set(item["consumers"]):
                fail(f"consumer ownership mismatch: {message_type}")
            if message_type == "legal.audit.fact.observed.v1":
                if set(sends[0].get("x-ueb-producer-services", [])) != set(config["audit_allowed_producers"]) or "audit-service" in sends[0].get("x-ueb-producer-services", []):
                    fail("audit producer exception is invalid")
            elif sends[0].get("x-ueb-service") != item["producer"]:
                fail(f"producer ownership mismatch: {message_type}")
        if not message_type.endswith(".v1") or item.get("ordering_key_field") != "aggregate_id" or item.get("ordering_fencing") != "aggregate_revision":
            fail(f"type/order metadata invalid: {message_type}")
        if not item.get("aggregate_id_field") or not item.get("aggregate_revision_field"):
            fail(f"missing aggregate relation map: {message_type}")

    planned_consumer_links = 0
    if {message_type: item.get("planned_consumers", []) for message_type, item in inventory.items() if item.get("planned_consumers")} != PLANNED_CONSUMERS:
        fail("planned consumer inventory differs from approved catalog")
    for message_type, item in inventory.items():
        component = components[item["component"]]
        if component.get("x-ueb-planned-consumers", []) != item.get("planned_consumers", []):
            fail(f"planned consumer extension differs from inventory: {message_type}")
    for message_type, planned in PLANNED_CONSUMERS.items():
        item = inventory[message_type]
        component = components[item["component"]]
        active_consumers = item["consumers"]
        planned_extension = component.get("x-ueb-planned-consumers", [])
        if planned_extension != planned or set(planned) & set(active_consumers):
            fail(f"planned consumer extension/disjointness invalid: {message_type}")
        if set(component.get("x-ueb-acl", {}).get("consume", [])) & set(planned):
            fail(f"planned consumer appears in active ACL: {message_type}")
        for _, operation in by_component.get(item["component"], []):
            if operation.get("x-ueb-service") in planned or operation.get("x-ueb-consumer-service") in planned:
                fail(f"planned consumer has an operation: {message_type}")
        planned_consumer_links += len(planned)

    deny = set(config["deny_property_tokens"])
    allowed = set(config["safe_property_exceptions"])
    for path in schema_paths:
        property_scan(docs[path.resolve()], deny, allowed, path.name)
        for property_name, property_schema in all_property_schemas(docs[path.resolve()]):
            if property_name.endswith("_hash") and not hash_schema_ok(property_schema):
                fail(f"hash property does not use HashValue: {path.name}:{property_name}")
    for group in ("valid",):
        for entry in manifest.get(group, []):
            payload = json_load(ROOT / entry["file"])
            def payload_keys(value: Any) -> None:
                if isinstance(value, dict):
                    for key, child in value.items():
                        check_key(key, deny, allowed, entry["file"]); payload_keys(child)
                elif isinstance(value, list):
                    for child in value: payload_keys(child)
            payload_keys(payload)

    for error in delivery_errors(policy):
        fail(f"delivery policy: {error}")
    canonical = policy.get("payload_hash_canonicalization", {})
    if canonical != {"algorithm": "SHA-256", "scope": "data", "encoding": "UTF-8", "object_keys": "recursively_sorted", "separators": ",:", "arrays": "preserve_order", "allowed_json_values": ["string", "integer", "boolean", "null"], "floats": "forbidden", "standard": "project_canonical_json_not_RFC_JCS"}:
        fail("payload hash canonicalization policy is incomplete")
    scenario_ids = {scenario.get("id") for scenario in scenarios.get("scenarios", [])}
    required_scenarios = {"duplicate-idempotent", "duplicate-altered-hash", "stale-revision", "revision-gap", "unpublish-dominates-publish", "revoke-dominates-activation", "artifacts-hash-mismatch", "unknown-type-version", "unauthorized-producer", "permanent-validation", "transient-bounded-retry", "dlq-replay-duplicate", "audit-outage-terminal", "feedback-not-golden", "golden-missing-approval", "revoke-after-freeze", "eligible-no-activation", "provider-secret-field", "forbidden-text-field", "later-injection"}
    scenario_checks = run_scenario_checks(valid_payloads, policy, spec, inventory, config["audit_allowed_producers"])
    scenario_check_names = {scenario.get("validator_check") for scenario in scenarios.get("scenarios", [])}
    if len(scenarios.get("scenarios", [])) < 15 or not required_scenarios <= scenario_ids:
        fail("delivery scenario coverage is incomplete")
    if None in scenario_check_names or scenario_check_names != set(scenario_checks):
        fail("delivery scenario validator_check inventory is incomplete or unknown")
    for name, passed in scenario_checks.items():
        if not passed:
            fail(f"delivery scenario check failed: {name}")

    edges = {(item["producer"], consumer) for item in inventory.values() if item["activation"] == "CORE" for consumer in item["consumers"] if item["producer"] != "MULTI_PRODUCER_EXCEPTION"}
    allowed_edges = {("document-service", "processing-service"), ("processing-service", "document-service"), ("processing-service", "index-service"), ("document-service", "index-service"), ("index-service", "document-service"), ("document-service", "citation-service")}
    if not edges <= allowed_edges:
        fail("undocumented active producer-consumer graph edge")
    if any(target == "audit-service" for _, target in edges):
        fail("audit must be terminal multi-producer exception")
    if not {"identity-service", "retrieval-service"} <= set(config["audit_allowed_producers"]):
        fail("audit allowlist is missing required producers")
    if not ownership_model_ok(spec, inventory, config["audit_allowed_producers"]):
        fail("directed exchange, ACL, or ownership model is invalid")

    # Deterministic in-memory mutation probes for non-schema delivery invariants.
    for mutation in (
        {**policy, "exactly_once": True},
        {key: value for key, value in policy.items() if key != "dlq"},
        {key: value for key, value in policy.items() if key != "retry"},
        {**policy, "ordering": {"scope": "global"}},
    ):
        if not delivery_errors(mutation):
            fail("delivery mutation unexpectedly accepted")

    summary = {
        "asyncapi_version": spec.get("asyncapi"), "schema_count": len(schema_paths), "message_count": len(components),
        "core_count": sum(1 for item in inventory.values() if item["activation"] == "CORE"),
        "later_count": sum(1 for item in inventory.values() if item["activation"] == "LATER"),
        "channel_count": len(channels), "operation_count": len(operations), "refs": refs,
        "valid_examples": valid_count, "invalid_schema_examples": invalid_schema_count,
        "invalid_semantic_examples": invalid_semantic_count, "scenario_count": len(scenarios.get("scenarios", [])),
        "scenario_checks": scenario_checks, "payload_hash_checks": payload_hash_checks,
        "aggregate_relation_checks": aggregate_relation_checks, "index_projection_checks": index_projection_checks,
        "planned_consumer_links": planned_consumer_links,
        "ownership_checks": "passed" if not ERRORS else "failed", "delivery_checks": "passed" if not ERRORS else "failed",
        "security_checks": "passed" if not ERRORS else "failed", "errors": ERRORS,
    }
    rendered = json.dumps(summary, sort_keys=True, separators=(",", ":"))
    if not ERRORS and report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if ERRORS else 0


if __name__ == "__main__":
    raise SystemExit(main())
