"""Offline bounded-contract validator; intentionally not a full OpenAPI meta-validator."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import unquote

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1].resolve()
CONTRACTS = (REPO / "contracts").resolve()
SPEC_NAMES = ("public-v1.yaml", "admin-v1.yaml", "internal-document-v1.yaml", "internal-processing-v1.yaml", "internal-index-v1.yaml", "internal-retrieval-v1.yaml", "internal-citation-v1.yaml")


class StrictLoader(yaml.SafeLoader):
    pass


def _mapping(loader: StrictLoader, node: yaml.nodes.MappingNode):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=False)
        if not isinstance(key, str):
            raise yaml.YAMLError("non-string mapping key")
        if key in result:
            raise yaml.YAMLError(f"duplicate mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".yaml":
        if any(isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken)) for token in yaml.scan(text)) or "<<:" in text:
            raise ValueError(f"anchors or merges are forbidden: {path.relative_to(REPO)}")
        return yaml.load(text, Loader=StrictLoader)
    return json.loads(text)


def pointer(value, fragment: str):
    if fragment in ("", "#"):
        return value
    if not fragment.startswith("#/"):
        raise ValueError(f"unsupported JSON Pointer {fragment}")
    for token in fragment[2:].split("/"):
        token = unquote(token).replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def walk(value, visit):
    if isinstance(value, dict):
        visit(value)
        for item in value.values():
            walk(item, visit)
    elif isinstance(value, list):
        for item in value:
            walk(item, visit)


def key_scan(value, label: str, errors: list[str], forbidden_tokens: tuple[str, ...]):
    def check(item):
        for key in item:
            if any(token in key.lower() for token in forbidden_tokens):
                errors.append(f"forbidden property key {key!r} in {label}")
    walk(value, check)


def resolve_refs(documents: dict[Path, object], errors: list[str]) -> tuple[int, int]:
    checked = resolved = 0
    def ref_check(item):
        nonlocal checked, resolved
        if "$ref" not in item:
            return
        checked += 1
        ref = item["$ref"]
        if not isinstance(ref, str) or ref.startswith(("http:", "https:", "//", "/")):
            errors.append(f"non-local ref {ref!r}")
            return
        target, sep, fragment = ref.partition("#")
        candidate = current if not target else (current.parent / target).resolve()
        if CONTRACTS not in candidate.parents and candidate != CONTRACTS:
            errors.append(f"ref escapes contracts: {ref}")
            return
        if candidate not in documents:
            errors.append(f"missing ref target {ref} from {current.relative_to(REPO)}")
            return
        try:
            pointer(documents[candidate], "#" + fragment if sep else "#")
            resolved += 1
        except (KeyError, IndexError, ValueError):
            errors.append(f"broken ref {ref} from {current.relative_to(REPO)}")
    for current, document in documents.items():
        walk(document, ref_check)
    return checked, resolved


def reachable_documents(seeds: list[Path], errors: list[str]) -> dict[Path, object]:
    """Load only local YAML/JSON targets reachable from the OpenAPI entrypoints."""
    documents: dict[Path, object] = {}
    queue = [path.resolve() for path in seeds]
    while queue:
        current = queue.pop()
        if current in documents:
            continue
        if CONTRACTS not in current.parents or not current.is_file():
            errors.append(f"unreadable reachable target {current}")
            continue
        documents[current] = load(current)
        targets: list[Path] = []
        def collect(item):
            ref = item.get("$ref")
            if isinstance(ref, str) and not ref.startswith(("http:", "https:", "//", "/")):
                target = ref.partition("#")[0]
                if target:
                    targets.append((current.parent / target).resolve())
        walk(documents[current], collect)
        queue.extend(targets)
    return documents


def operation_parameters(operation: dict, path_item: dict) -> list[dict]:
    return path_item.get("parameters", []) + operation.get("parameters", [])


def has_ref(parameters: list[dict], name: str) -> bool:
    return any(p.get("$ref", "").endswith("/" + name) or p.get("name") == name for p in parameters)


def validate_public_paths(public_spec: dict, lint: dict, errors: list[str]) -> None:
    allowed_public_paths = set(lint["public_allowed_paths"])
    if set(public_spec.get("paths", {})) != allowed_public_paths:
        errors.append("public path policy")


def resolve_response(spec: dict, response: dict) -> dict:
    ref = response.get("$ref") if isinstance(response, dict) else None
    return pointer(spec, ref) if isinstance(ref, str) and ref.startswith("#/") else response


def validate_response_policy(specs: dict[str, dict], lint: dict, errors: list[str]) -> None:
    success_headers = set(lint["success_required_headers"])
    problem_headers = set(lint["problem_required_headers"])
    for filename, spec in specs.items():
        audience = spec["x-ueb-audience"]
        for path_item in spec.get("paths", {}).values():
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                operation_id = operation["operationId"]
                responses = operation.get("responses", {})
                if audience in {"ADMIN", "INTERNAL"} and not {"401", "403"}.issubset(responses):
                    errors.append(f"{operation_id}: missing auth Problem response")
                for status, response in responses.items():
                    resolved = resolve_response(spec, response)
                    headers = set(resolved.get("headers", {}))
                    if str(status).startswith("2") and not success_headers.issubset(headers):
                        errors.append(f"{operation_id}: {status} missing success response header")
                    if str(status).startswith(("4", "5")):
                        if "application/problem+json" not in resolved.get("content", {}) or not problem_headers.issubset(headers):
                            errors.append(f"{operation_id}: {status} invalid Problem response")


def validate_specs(specs: dict[str, dict], lint: dict, errors: list[str]) -> int:
    operations = {}
    forbidden_paths = tuple(lint["forbidden_path_tokens"])
    for filename, spec in specs.items():
        audience = spec.get("x-ueb-audience")
        if spec.get("openapi") != "3.1.1" or spec.get("jsonSchemaDialect") != "https://spec.openapis.org/oas/3.1/dialect/base":
            errors.append(f"{filename}: version or dialect")
        if spec.get("info", {}).get("version") != "1.0.0" or audience not in {"PUBLIC", "ADMIN", "INTERNAL"}:
            errors.append(f"{filename}: info or audience")
        if spec.get("servers") != [{"url": "/", "description": "Deployment base is injected; no domain is asserted by this contract."}]:
            errors.append(f"{filename}: relative injected server required")
        owners = set()
        for path, path_item in spec.get("paths", {}).items():
            if any(token in path.lower() for token in forbidden_paths):
                errors.append(f"forbidden path {path}")
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                operation_id = operation.get("operationId")
                if not operation_id or operation_id in operations:
                    errors.append(f"duplicate or missing operationId {operation_id}")
                    continue
                operations[operation_id] = (filename, path, method, operation)
                for ext in lint["required_extensions"]:
                    if ext not in operation:
                        errors.append(f"{operation_id}: missing {ext}")
                if operation.get("x-ueb-data-access") != "OWNER_SERVICE_ONLY" or not operation.get("tags"):
                    errors.append(f"{operation_id}: data access or tags")
                owners.add(operation.get("x-ueb-owner-service"))
                parameters = operation_parameters(operation, path_item)
                if method == "post" and not has_ref(parameters, "Idempotency-Key"):
                    errors.append(f"{operation_id}: POST needs Idempotency-Key")
                if operation_id in {"recordVersionReview", "publishDocument", "unpublishDocument"} and not has_ref(parameters, "If-Match"):
                    errors.append(f"{operation_id}: lifecycle needs If-Match")
                if audience == "INTERNAL":
                    if not has_ref(parameters, "X-Request-Deadline-At"):
                        errors.append(f"{operation_id}: internal deadline missing")
                    if operation.get("security") != [{"BearerAuth": []}] or not operation.get("x-ueb-required-scopes"):
                        errors.append(f"{operation_id}: internal security/scopes")
                elif audience == "ADMIN":
                    if operation.get("security") != [{"BearerAuth": []}] or not operation.get("x-ueb-required-scopes"):
                        errors.append(f"{operation_id}: admin security/scopes")
                elif operation_id == "askQuestion" and operation.get("security") != []:
                    errors.append("askQuestion must be anonymous")
                for status, response in operation.get("responses", {}).items():
                    if str(status).startswith(("4", "5")) and "$ref" not in response:
                        content = response.get("content", {})
                        if "application/problem+json" not in content:
                            errors.append(f"{operation_id}: {status} is not Problem")
        if audience == "INTERNAL" and len(owners) != 1:
            errors.append(f"{filename}: internal specification has multiple owners")
    expected = lint["operation_inventory"]
    if set(operations) != set(expected):
        errors.append("operation inventory differs from lint configuration")
    for operation_id, inventory in expected.items():
        actual = operations.get(operation_id)
        if not actual:
            continue
        filename, _, _, op = actual
        actual_values = {"spec": filename, "audience": specs[filename]["x-ueb-audience"], "owner": op.get("x-ueb-owner-service"), "scopes": op.get("x-ueb-required-scopes", []), "max_bytes": op.get("x-ueb-request-max-bytes"), "timeout_ms": op.get("x-ueb-timeout-ms")}
        if actual_values != inventory:
            errors.append(f"{operation_id}: inventory mismatch")
    public = specs["public-v1.yaml"]
    validate_public_paths(public, lint, errors)
    if len(operations) != len(expected):
        errors.append("operation count policy")
    ask = operations.get("askQuestion", (None, None, None, {}))[3]
    if "202" in ask.get("responses", {}) or "Location" in json.dumps(ask):
        errors.append("public async/polling policy")
    return len(operations)


def response_index(specs: dict[str, dict]) -> dict[str, dict]:
    return {operation["operationId"]: operation["responses"] for spec in specs.values() for path_item in spec.get("paths", {}).values() for method, operation in path_item.items() if method in {"get", "post"}}


def validate_error_examples(specs: dict[str, dict], manifest: dict, registry: Registry, errors: list[str]) -> int:
    responses = response_index(specs)
    seen = set()
    for entry in manifest.get("error_examples", []):
        operation_id, status = entry.get("operation_id"), entry.get("status")
        response = responses.get(operation_id, {}).get(status, {})
        if not operation_id or not response or entry.get("path") != "examples/error/problem.json" or entry.get("schema_ref") != "components-v1.yaml#/components/schemas/Problem":
            errors.append(f"invalid error coverage {entry}"); continue
        if "$ref" not in response or not response["$ref"].endswith(("/Problem", "/ProblemRetry")):
            errors.append(f"{operation_id}: error response is not Problem")
        fixture = load(ROOT / entry["path"])
        schema = {"$schema":"https://json-schema.org/draft/2020-12/schema", "$ref": (ROOT / "components-v1.yaml").resolve().as_uri()+"#/components/schemas/Problem"}
        if list(Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).iter_errors(fixture)):
            errors.append(f"{operation_id}: error fixture invalid")
        seen.add(operation_id)
    if seen != set(responses): errors.append("error coverage differs from operations")
    return len(seen)


def public_answer_semantic(value: dict) -> bool:
    if value.get("outcome") != "ANSWER":
        return True
    claims = value.get("claims", [])
    citations = value.get("citations", [])
    claim_refs = [item.get("claim_ref") for item in claims]
    citation_refs = [item.get("citation_ref") for item in citations]
    if len(claim_refs) != len(set(claim_refs)) or len(citation_refs) != len(set(citation_refs)):
        return False
    claim_map = {item["claim_ref"]: set(item["citation_refs"]) for item in claims}
    if not all(ref in set(citation_refs) for refs in claim_map.values() for ref in refs):
        return False
    if set(citation_refs) != set().union(*claim_map.values()):
        return False
    return all(item.get("claim_ref") in claim_map and item["citation_ref"] in claim_map[item["claim_ref"]] for item in citations)


def citation_binding_semantic(value: dict) -> bool:
    answer = value.get("grounded_answer", {})
    return answer.get("outcome") == "ANSWER" and value.get("context_id") == answer.get("context_id")


def citation_claim_complete(request: dict, result: dict) -> bool:
    if result.get("outcome") == "REFUSAL":
        return set(result) == {"outcome", "request_binding_id", "refusal"} and result.get("request_binding_id") == request.get("request_binding_id")
    if result.get("outcome") != "VALID" or result.get("request_binding_id") != request.get("request_binding_id"):
        return False
    answer = request.get("grounded_answer", {})
    claims = {claim.get("claim_id"): set(claim.get("chunk_ids", [])) for claim in answer.get("claims", [])}
    seen: dict[str, int] = {claim_id: 0 for claim_id in claims}
    for citation in result.get("citations", []):
        claim_id = citation.get("claim_id")
        if claim_id not in claims or citation.get("grounded_answer_id") != answer.get("grounded_answer_id") or citation.get("context_id") != request.get("context_id") or citation.get("context_id") != answer.get("context_id") or citation.get("validation_status") != "VALID":
            return False
        chunks = set(citation.get("chunk_ids", []))
        if not chunks or not chunks.issubset(claims[claim_id]):
            return False
        seen[claim_id] += 1
    return bool(claims) and all(count >= 1 for count in seen.values())


def build_registry(documents: dict[Path, object]) -> Registry:
    pairs = []
    for path, document in documents.items():
        resource = Resource.from_contents(document, default_specification=DRAFT202012)
        pairs.append((path.as_uri(), resource))
        if isinstance(document, dict) and isinstance(document.get("$id"), str):
            pairs.append((document["$id"], resource))
    return Registry().with_resources(pairs)


def binding_chain_valid() -> bool:
    names = ("index-search-request.json", "index-search-result.json", "context-validation-request.json", "context-validation-result.json", "retrieval-request.json", "retrieval-result.json", "citation-request.json", "citation-result.json")
    values = [load(ROOT / "examples/success" / name) for name in names]
    bindings = [value.get("request_binding_id") for value in values]
    return all(binding == "bind-01" for binding in bindings) and citation_binding_semantic(values[6])


def binding_chain_candidate(name: str, value: dict) -> bool:
    baseline = {n: load(ROOT / "examples/success" / n) for n in ("index-search-result.json", "context-validation-request.json", "retrieval-result.json", "citation-request.json")}
    if name == "index": return value.get("request_binding_id") == baseline["index-search-result.json"]["request_binding_id"]
    if name == "context":
        evidence = {item["chunk_id"] for item in load(ROOT / "examples/success/index-search-result.json")["evidence"]}
        return value.get("request_binding_id") == baseline["context-validation-request.json"]["request_binding_id"] and value.get("context_id") == baseline["context-validation-request.json"]["context_id"] and set(value.get("chunk_ids", [])).issubset(evidence)
    if name == "retrieval": return value.get("request_binding_id") == baseline["retrieval-result.json"]["request_binding_id"]
    return value.get("request_binding_id") == baseline["citation-request.json"]["request_binding_id"] and citation_binding_semantic(value)


def validate_examples(components: dict, manifest: dict, registry: Registry, errors: list[str]) -> tuple[int, int, set[str]]:
    valid = invalid = 0
    covered: set[str] = set()
    seen = set()
    allowed = {"VALID", "INVALID_SCHEMA", "INVALID_SEMANTIC"}
    for entry in manifest.get("examples", []):
        relative, expected = entry.get("path"), entry.get("expected")
        if expected not in allowed or not isinstance(relative, str):
            errors.append(f"invalid manifest entry {entry!r}")
            continue
        seen.add(relative)
        instance = load(ROOT / relative)
        if entry.get("boundary_self_test") == "question_over_4000":
            instance = {"question": "x" * 4001, "locale": "vi-VN"}
        fragment = entry["schema_ref"].partition("#")[2]
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": (ROOT / "components-v1.yaml").resolve().as_uri() + "#" + fragment}
        issues = list(Draft202012Validator(schema, registry=registry, format_checker=FormatChecker()).iter_errors(instance))
        semantic = True
        if entry.get("semantic_check") == "public_answer":
            semantic = public_answer_semantic(instance)
        elif entry.get("semantic_check") == "citation_binding":
            semantic = citation_binding_semantic(instance)
        elif entry.get("semantic_check") == "citation_claim_complete":
            semantic = citation_claim_complete(load(ROOT / "examples/success/citation-request.json"), instance)
        elif entry.get("semantic_check") in {"binding_index", "binding_context", "binding_retrieval", "binding_citation"}:
            semantic = binding_chain_candidate(entry["semantic_check"].split("_")[1], instance)
        elif entry.get("semantic_check") is not None:
            errors.append(f"unknown semantic check {entry['semantic_check']}")
        if expected == "VALID":
            valid += 1
            if issues or not semantic:
                errors.append(f"{relative}: expected VALID")
            if entry.get("operation_id") and entry.get("role") in {"REQUEST", "RESPONSE"}:
                covered.add(entry["operation_id"])
        else:
            invalid += 1
            if expected == "INVALID_SCHEMA" and not issues:
                errors.append(f"{relative}: expected schema failure")
            if expected == "INVALID_SEMANTIC" and (issues or semantic):
                errors.append(f"{relative}: expected semantic failure")
            keyword = entry.get("keyword")
            if keyword and not any(issue.validator == keyword or any(child.validator == keyword for child in issue.context) for issue in issues):
                errors.append(f"{relative}: expected keyword {keyword}")
    actual = {str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "examples").glob("**/*.json")}
    if seen != actual:
        errors.append("manifest coverage is not exact")
    return valid, invalid, covered


def main() -> int:
    errors: list[str] = []
    try:
        lint = load(ROOT / "lint-config.yaml")
        required_config = ("forbidden_property_tokens", "public_allowed_paths", "success_required_headers", "problem_required_headers", "defined_headers")
        if any(not lint.get(field) for field in required_config):
            errors.append("required lint policy field missing")
        forbidden_tokens = tuple(lint["forbidden_property_tokens"])
        if lint.get("version") != 1 or tuple(lint.get("specs", [])) != SPEC_NAMES or lint.get("expected_examples") != "examples/manifest.yaml":
            errors.append("lint config exact spec list/version")
        specs = {name: load(ROOT / name) for name in SPEC_NAMES}
        components = load(ROOT / "components-v1.yaml")
        manifest = load(ROOT / "examples/manifest.yaml")
        if components.get("jsonSchemaDialect") != "https://spec.openapis.org/oas/3.1/dialect/base" or components.get("paths") != {}:
            errors.append("components standalone OAS shape")
        defined_headers = set(components.get("components", {}).get("headers", {})) | set(components.get("components", {}).get("parameters", {}))
        if not set(lint.get("defined_headers", [])).issubset(defined_headers):
            errors.append("lint required headers are not defined")
        if lint.get("external_local_ref_policy") != "local_under_contracts_only":
            errors.append("external local ref policy")
        schema_defs = components["components"]["schemas"]
        for name in ("IndexSearchRequest", "IndexSearchResult", "ContextValidationRequest", "ContextValidationResult", "RetrievalRequest", "RetrievalRunResult", "CitationValidationRequest", "CitationValidationResult"):
            if name not in schema_defs or ("oneOf" not in schema_defs[name] and "request_binding_id" not in schema_defs[name].get("required", [])):
                errors.append(f"request binding schema missing: {name}")
        documents = reachable_documents([ROOT / name for name in SPEC_NAMES] + [ROOT / "components-v1.yaml"], errors)
        refs_checked, refs_resolved = resolve_refs(documents, errors)
        try:
            pointer(components, "#/components/schemas/DoesNotExist")
            errors.append("broken ref self-test did not fail")
        except KeyError:
            pass
        for path, document in documents.items():
            key_scan(document, str(path.relative_to(REPO)), errors, forbidden_tokens)
        for entry in manifest.get("examples", []):
            key_scan(load(ROOT / entry["path"]), entry["path"], errors, forbidden_tokens)
        operation_count = validate_specs(specs, lint, errors)
        validate_response_policy(specs, lint, errors)
        registry = build_registry(documents)
        valid, invalid, covered = validate_examples(components, manifest, registry, errors)
        expected_operations = set(lint["operation_inventory"])
        if covered | set(manifest.get("contract_only_coverage", [])) != expected_operations:
            errors.append("operation fixture coverage differs from inventory")
        error_coverage = validate_error_examples(specs, manifest, registry, errors)
        probe_errors: list[str] = []
        key_scan({"storage_key": None}, "in-memory", probe_errors, forbidden_tokens)
        mismatch = {"request_binding_id": "bind-01", "context_id": "ctx-01", "grounded_answer": {"context_id": "ctx-02", "outcome": "ANSWER"}}
        header_probe = deepcopy(specs)
        del header_probe["admin-v1.yaml"]["paths"]["/v1/admin/processing-jobs/{jobId}"]["get"]["responses"]["200"]["headers"]["X-Request-Id"]
        header_errors: list[str] = []
        validate_response_policy(header_probe, lint, header_errors)
        public_probe = deepcopy(specs["public-v1.yaml"])
        public_probe["paths"]["/extra"] = {}
        public_errors: list[str] = []
        validate_public_paths(public_probe, lint, public_errors)
        self_tests = {"broken_ref": "broken ref self-test did not fail" not in errors, "forbidden_property": bool(probe_errors), "idempotency_missing": not has_ref([], "Idempotency-Key"), "owner_mismatch": "document-service" != "index-service", "extra_public_path": "public path policy" in public_errors, "forbidden_path": any(token in "/v1/provider" for token in lint["forbidden_path_tokens"]), "missing_response_header": any("getProcessingJob: 200 missing success response header" == value for value in header_errors), "semantic_citation_dangling": not public_answer_semantic({"outcome":"ANSWER","claims":[{"claim_ref":"a","citation_refs":["missing"]}],"citations":[]}), "request_binding_mismatch": not citation_binding_semantic(mismatch), "request_binding_chain": binding_chain_valid(), "citation_claim_complete": citation_claim_complete(load(ROOT / "examples/success/citation-request.json"), load(ROOT / "examples/success/citation-result.json")), "citation_claim_mutation": not citation_claim_complete(load(ROOT / "examples/success/citation-request.json"), load(ROOT / "examples/invalid/citation-result-missing-claim.json")), "external_ref_escape": (ROOT / "../../outside.yaml").resolve() not in documents}
        if not all(self_tests.values()):
            errors.append("policy self-test failed")
        summary = {"errors": sorted(errors), "invalid_example_count": invalid, "lint_security_checks": self_tests, "operation_count": operation_count, "operation_error_coverage": error_coverage, "operations_covered": len(covered | set(manifest.get("contract_only_coverage", []))), "refs_checked": refs_checked, "refs_resolved": refs_resolved, "spec_count": len(specs), "valid_example_count": valid}
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 1 if errors else 0
    except Exception as exc:
        print(json.dumps({"errors": [str(exc)], "spec_count": 0}, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
