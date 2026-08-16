"""Offline validator for append-only decision revision candidates."""
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


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "contracts" / "governance"
CONFIG_PATH = GOVERNANCE / "decision-revisions.yaml"
DEFAULT_OUTPUT = GOVERNANCE / "validation-report.json"


class StrictLoader(yaml.SafeLoader):
    pass


def _mapping(loader: StrictLoader, node: yaml.nodes.MappingNode) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=False)
        if not isinstance(key, str):
            raise yaml.YAMLError("non-string mapping key")
        if key in result:
            raise yaml.YAMLError(f"duplicate mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def strict_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if any(isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken)) for token in yaml.scan(text)) or "<<:" in text:
        raise ValueError(f"anchors or merges are forbidden: {path.relative_to(ROOT)}")
    value = yaml.load(text, Loader=StrictLoader)
    if not isinstance(value, dict):
        raise ValueError("governance document must be a mapping")
    return value


def entry_text(decision_log: str, append_id: str) -> str:
    match = re.search(rf"^### {re.escape(append_id)}\n.*?(?=^### |\Z)", decision_log, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"missing immutable historical entry {append_id}")
    return match.group(0)


def dependency_closure(prompts: dict[str, Any], start: str) -> set[str]:
    seen: set[str] = set()
    todo = [start]
    while todo:
        prompt = todo.pop()
        if prompt in seen:
            continue
        seen.add(prompt)
        item = prompts.get(prompt)
        if not isinstance(item, dict):
            continue
        dependencies = item.get("dependencies", [])
        if isinstance(dependencies, list):
            todo.extend(value for value in dependencies if isinstance(value, str))
    seen.discard(start)
    return seen


def validate(config: dict[str, Any], decision_log: str, manifest: dict[str, Any], state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if config.get("version") != 1 or config.get("format") != "decision_revision_governance":
        errors.append("version or format")
    if config.get("yaml_policy") != {"aliases_forbidden": True, "duplicate_keys_forbidden": True}:
        errors.append("strict YAML policy")

    current = config.get("current_prompt", {})
    prompt_state = state.get("prompts", {}).get("02.7", {}) if isinstance(state.get("prompts"), dict) else {}
    resolution = config.get("effective_resolution", {})
    if (not isinstance(current, dict) or current.get("id") != "02.7"
            or current.get("approval_binds") != "current_revision_artifacts"
            or prompt_state.get("status") not in {"IN_PROGRESS", "AWAITING_APPROVAL"}):
        errors.append("current prompt candidate state")
    if (not isinstance(resolution, dict)
            or resolution.get("candidate_effective_now") is not False
            or resolution.get("candidate_effective_if_current_prompt_approved") is not True
            or resolution.get("old_entries") != "immutable"):
        errors.append("root candidate effective semantics")

    expected = {"DEC-005": ("DEC-005", "DEC-005@1", "DEC-005@2", "DEC-015"), "DEC-007": ("DEC-007", "DEC-007@1", "DEC-007@2", "DEC-016")}
    chains = config.get("chains", [])
    if not isinstance(chains, list) or {item.get("decision_key") for item in chains if isinstance(item, dict)} != set(expected):
        errors.append("chain uniqueness")
    for chain in chains if isinstance(chains, list) else []:
        if not isinstance(chain, dict):
            continue
        key = chain.get("decision_key")
        if key not in expected:
            continue
        historic_append, historic_id, candidate_id, candidate_append = expected[key]
        revisions = chain.get("revisions", [])
        if not isinstance(revisions, list) or [item.get("revision_id") for item in revisions if isinstance(item, dict)] != [historic_id, candidate_id]:
            errors.append(f"{key}: revision chain")
            continue
        historic, candidate = revisions
        if historic.get("append_id") != historic_append or historic.get("historical_integrity") != "LEGACY_UNKNOWN_HASH":
            errors.append(f"{key}: legacy marker")
        try:
            observed = hashlib.sha256(entry_text(decision_log, historic_append).encode("utf-8")).hexdigest()
            if historic.get("current_observed_sha256") != observed:
                errors.append(f"{key}: mutable history")
        except ValueError as exc:
            errors.append(str(exc))
        if candidate.get("revision_id") != candidate_id or candidate.get("append_id") != candidate_append or candidate.get("supersedes") != historic_id:
            errors.append(f"{key}: missing or invalid supersedes")
        if candidate.get("status") != "PROPOSED_PENDING_HUMAN_APPROVAL" or candidate.get("effective_at") is not None or candidate.get("effective_on") != "human approval of Prompt 02.7 current revision":
            errors.append(f"{key}: candidate effective semantics")
        if key == "DEC-007":
            policy = candidate.get("reopen_policy", {})
            if not isinstance(policy, dict) or policy.get("supports_terminal_statuses") != ["PASS", "FAIL"] or policy.get("approval_archive") != "distinct_append_only" or policy.get("rejection_archive") != "distinct_append_only" or policy.get("revision_increment") != "required" or policy.get("fail_is_effective_approval") is not False or policy.get("direct_bypass") != "forbidden":
                errors.append("DEC-007: reopen policy")

    prompts = manifest.get("prompts", {}) if isinstance(manifest, dict) else {}
    dependency = config.get("manifest_dependency", {})
    if not isinstance(dependency, dict) or not isinstance(prompts, dict):
        errors.append("manifest dependency data")
    else:
        item = prompts.get("05.8", {})
        closure = dependency_closure(prompts, "05.8")
        if item.get("dependencies") != dependency.get("direct_dependencies") or not set(dependency.get("transitively_reaches", [])).issubset(closure) or closure.intersection(set(dependency.get("must_not_reach", []))):
            errors.append("provider dependency restored or manifest closure mismatch")
        for edge in dependency.get("preserved_edges", []):
            if not isinstance(edge, list) or len(edge) != 2 or prompts.get(edge[0], {}).get("dependencies") != [edge[1]]:
                errors.append("preserved manifest edge")
                break

    if "| provider-service |" not in (ROOT / "docs/architecture/container-map.md").read_text(encoding="utf-8") or "| provider-service | Provider config" not in (ROOT / "docs/architecture/container-map.md").read_text(encoding="utf-8"):
        errors.append("provider architecture evidence")
    evidence = config.get("evidence", {})
    if not isinstance(evidence, dict):
        errors.append("evidence mapping")
    else:
        for name, relative in evidence.items():
            if name == "commit":
                if relative is not None:
                    errors.append("placeholder commit")
            elif not isinstance(relative, str) or not (ROOT / relative).is_file():
                errors.append(f"missing evidence {name}")
    for marker in config.get("required_markers", []):
        if not isinstance(marker, str) or marker not in decision_log:
            errors.append(f"missing decision marker {marker}")
    return errors


def negative_mutation_results(config: dict[str, Any], decision_log: str, manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, bool]:
    def rejected(mutator) -> bool:
        candidate = copy.deepcopy(config)
        log = decision_log
        altered_manifest = copy.deepcopy(manifest)
        mutator(candidate, altered_manifest)
        return bool(validate(candidate, log, altered_manifest, state))

    return {
        "candidate_marked_effective_now": rejected(lambda cfg, _: cfg["chains"][0]["revisions"][1].update({"effective_at": "2026-08-16T00:00:00+00:00"})),
        "root_candidate_marked_effective_now": rejected(lambda cfg, _: cfg["effective_resolution"].update({"candidate_effective_now": True})),
        "approval_binding_changed": rejected(lambda cfg, _: cfg["current_prompt"].update({"approval_binds": "any_revision"})),
        "missing_supersedes": rejected(lambda cfg, _: cfg["chains"][0]["revisions"][1].pop("supersedes")),
        "provider_dependency_restored": rejected(lambda _, doc: doc["prompts"]["05.8"].update({"dependencies": ["05.7"]})),
        "historical_digest_mutated": rejected(lambda cfg, _: cfg["chains"][0]["revisions"][0].update({"current_observed_sha256": "0" * 64})),
        "historical_decision_log_mutated": bool(validate(config, decision_log.replace("### DEC-005\n", "### DEC-005\nMUTATED\n", 1), manifest, state)),
        "fail_treated_as_approval": rejected(lambda cfg, _: cfg["chains"][1]["revisions"][1]["reopen_policy"].update({"fail_is_effective_approval": True})),
        "missing_evidence": rejected(lambda cfg, _: cfg["evidence"].update({"verify_pack": "scripts/missing.py"})),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output != DEFAULT_OUTPUT.resolve():
        parser.error("--output is restricted to contracts/governance/validation-report.json")
    try:
        config = strict_yaml(CONFIG_PATH)
        decision_log = (ROOT / "docs/decision-log.md").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "prompts/manifest.json").read_text(encoding="utf-8"))
        state = json.loads((ROOT / ".agent-run/prompt-state.json").read_text(encoding="utf-8"))
        errors = validate(config, decision_log, manifest, state)
        self_tests = negative_mutation_results(config, decision_log, manifest, state)
        if not all(self_tests.values()):
            errors.append("negative mutation self-test")
        summary = {"chains": 2, "effective_if_current_prompt_approved": True, "effective_now": False, "errors": sorted(errors), "negative_mutation_checks": self_tests}
    except Exception as exc:
        summary = {"chains": 0, "effective_if_current_prompt_approved": False, "effective_now": False, "errors": [str(exc)], "negative_mutation_checks": {}}
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
