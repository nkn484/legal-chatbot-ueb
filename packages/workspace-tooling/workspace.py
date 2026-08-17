"""Fail-closed, standard-library tooling for the Prompt 03.1 skeleton."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SKELETON_FILES = frozenset({"README.md", "component.toml"})
AUDIT_RUNTIME_FILES = frozenset(
    {
        "README.md",
        ".gitignore",
        "component.toml",
        "pyproject.toml",
        "requirements.in",
        "requirements.txt",
        "requirements-dev.in",
        "requirements-dev.txt",
        "src/audit_service/__init__.py",
        "src/audit_service/app.py",
        "src/audit_service/context.py",
        "src/audit_service/health.py",
        "src/audit_service/http_client.py",
        "src/audit_service/logging.py",
        "src/audit_service/main.py",
        "src/audit_service/middleware.py",
        "src/audit_service/migrations.py",
        "src/audit_service/settings.py",
        "tests/test_runtime.py",
    }
)
GENERATED_FILES = frozenset({"README.md", "package.toml", "contracts-index.json"})
TOOLING_FILES = frozenset(
    {
        "README.md",
        "package.toml",
        "workspace.py",
        "templates/fastapi-service/README.md.template",
        "templates/fastapi-service/.gitignore.template",
        "templates/fastapi-service/pyproject.toml.template",
        "templates/fastapi-service/requirements.in.template",
        "templates/fastapi-service/requirements-dev.in.template",
        "templates/fastapi-service/src/template_service/__init__.py",
        "templates/fastapi-service/src/template_service/app.py",
        "templates/fastapi-service/src/template_service/context.py",
        "templates/fastapi-service/src/template_service/health.py",
        "templates/fastapi-service/src/template_service/http_client.py",
        "templates/fastapi-service/src/template_service/logging.py",
        "templates/fastapi-service/src/template_service/main.py",
        "templates/fastapi-service/src/template_service/middleware.py",
        "templates/fastapi-service/src/template_service/migrations.py",
        "templates/fastapi-service/src/template_service/settings.py",
    }
)
ALLOWED_DEPENDENCIES = ["packages/generated-contracts"]


@dataclass(frozen=True)
class Component:
    identifier: str
    kind: str
    status: str
    path: str
    bounded_context: str
    data_ownership: str


COMPONENTS = (
    Component("api-gateway", "service", "CORE", "services/api-gateway", "Transport routing and verified auth context", "Self-only transport policy state; no business data"),
    Component("identity-service", "service", "CORE", "services/identity-service", "Identity, credentials, sessions, roles, permissions, and service identity", "Self-only identity and access data"),
    Component("audit-service", "service", "CORE", "services/audit-service", "Append-only audit integrity, retention, and query", "Self-only append-only audit data"),
    Component("document-service", "service", "CORE", "services/document-service", "Immutable document/version and canonical legal metadata", "Self-only document, version, and canonical metadata"),
    Component("processing-service", "service", "CORE", "services/processing-service", "Extraction, normalization, chunks, locators, and quality review", "Self-only processing jobs and derived artifact references"),
    Component("index-service", "service", "CORE", "services/index-service", "FTS projection and index lifecycle", "Self-only index projections and index state"),
    Component("retrieval-service", "service", "CORE", "services/retrieval-service", "Query normalization, retrieval runs, ranking, and sufficiency", "Self-only retrieval runs and configuration"),
    Component("citation-service", "service", "CORE", "services/citation-service", "Citation validation and canonical source rendering", "Self-only citation validation runs"),
    Component("chat-service", "service", "CORE", "services/chat-service", "Conversation, answer/refusal snapshots, and idempotency", "Self-only conversation and immutable answer/refusal snapshots"),
    Component("provider-service", "service", "LATER", "services/provider-service", "Provider configuration, secret references, lifecycle, and adapter", "Self-only provider configuration and secret references"),
    Component("feedback-service", "service", "LATER", "services/feedback-service", "Feedback, annotation, and Golden Answer lifecycle", "Self-only feedback, annotation, and Golden Answer data"),
    Component("evaluation-service", "service", "LATER", "services/evaluation-service", "Frozen datasets, evaluation runs, metrics, and candidate gate", "Self-only dataset, evaluation, and candidate metadata"),
    Component("web-chat", "app", "CLIENT", "apps/web-chat", "Web Chat client", "Self-only client-local state; no service-owned data"),
    Component("admin-portal", "app", "CLIENT", "apps/admin-portal", "Admin Portal client", "Self-only client-local state; no service-owned data"),
)


class ValidationError(RuntimeError):
    """Raised whenever an invariant cannot be proven locally."""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def component_by_path(raw_path: str) -> Component:
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError(f"component target must be a workspace-relative component path: {raw_path}")
    normalized = candidate.as_posix().rstrip("/")
    for component in COMPONENTS:
        if component.path == normalized:
            return component
    raise ValidationError(f"unknown component target: {raw_path}")


def regular_relative_files(directory: Path) -> set[str]:
    if not directory.is_dir():
        raise ValidationError(f"missing directory: {directory.relative_to(ROOT).as_posix()}")
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file()
        and not {
            "__pycache__",
            ".mypy_cache",
            ".ruff_cache",
            "build",
            "dist",
        }.intersection(path.parts)
        and not any(part.endswith(".egg-info") for part in path.parts)
        and path.suffix != ".pyc"
    }


def read_manifest(component: Component) -> dict[str, Any]:
    manifest_path = ROOT / component.path / "component.toml"
    try:
        parsed = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValidationError(f"invalid manifest {component.path}/component.toml: {error}") from error
    if set(parsed) != {"component"} or not isinstance(parsed["component"], dict):
        raise ValidationError(f"invalid manifest table in {component.path}")
    manifest = parsed["component"]
    expected = {
        "id": component.identifier,
        "kind": component.kind,
        "status": component.status,
        "path": component.path,
        "build_artifact": (
            "audit-service-runtime.zip"
            if component.identifier == "audit-service"
            else f"{component.identifier}-skeleton.zip"
        ),
        "allowed_workspace_dependencies": ALLOWED_DEPENDENCIES,
    }
    if manifest != expected:
        raise ValidationError(f"manifest does not exactly declare its skeleton boundary: {component.path}")
    return manifest


def validate_component(component: Component) -> dict[str, Any]:
    directory = ROOT / component.path
    files = regular_relative_files(directory)
    expected_files = AUDIT_RUNTIME_FILES if component.identifier == "audit-service" else SKELETON_FILES
    if files != expected_files:
        raise ValidationError(
            f"unexpected business/runtime file or missing skeleton file in {component.path}: "
            f"expected {sorted(expected_files)}, found {sorted(files)}"
        )
    return read_manifest(component)


def contract_tree_metadata() -> dict[str, Any]:
    contracts = ROOT / "contracts"
    if not contracts.is_dir():
        raise ValidationError("canonical contracts directory is missing")
    rows = []
    for path in sorted(contracts.rglob("*")):
        if path.is_file():
            rows.append((path.relative_to(contracts).as_posix(), sha256_bytes(path.read_bytes())))
    aggregate = "".join(f"{path}\0{digest}\n" for path, digest in rows).encode("utf-8")
    return {
        "format": "canonical-contracts-index-v1",
        "hash_algorithm": "sha256",
        "source_file_count": len(rows),
        "source_root": "contracts",
        "source_tree_sha256": sha256_bytes(aggregate),
    }


def validate_generated_contracts() -> None:
    package = ROOT / "packages" / "generated-contracts"
    if regular_relative_files(package) != GENERATED_FILES:
        raise ValidationError("generated-contracts must contain only its metadata boundary files")
    try:
        package_metadata = tomllib.loads((package / "package.toml").read_text(encoding="utf-8"))
        index = json.loads((package / "contracts-index.json").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid generated-contracts metadata: {error}") from error
    expected_package = {
        "package": {
            "id": "generated-contracts",
            "kind": "generated-contract-boundary",
            "generated_only": True,
            "source": "contracts",
            "allowed_workspace_dependencies": [],
        }
    }
    if package_metadata != expected_package:
        raise ValidationError("generated-contracts package metadata is invalid")
    if index != contract_tree_metadata():
        raise ValidationError("generated-contracts index/hash metadata is stale or invalid")


def validate_packages() -> None:
    packages = ROOT / "packages"
    if not packages.is_dir():
        raise ValidationError("packages directory is missing")
    package_names = {entry.name for entry in packages.iterdir() if entry.is_dir()}
    allowed = {"generated-contracts", "workspace-tooling"}
    if package_names != allowed:
        raise ValidationError(f"forbidden shared runtime package or missing required package: {sorted(package_names)}")
    tooling = packages / "workspace-tooling"
    if regular_relative_files(tooling) != TOOLING_FILES:
        raise ValidationError("workspace-tooling contains unexpected files")
    try:
        tooling_metadata = tomllib.loads((tooling / "package.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValidationError(f"invalid workspace-tooling metadata: {error}") from error
    if tooling_metadata != {
        "package": {
            "id": "workspace-tooling",
            "kind": "development-tooling",
            "runtime": "python-stdlib-only",
            "allowed_workspace_dependencies": [],
        }
    }:
        raise ValidationError("workspace-tooling metadata is invalid")
    validate_generated_contracts()


def validate_component_inventory() -> None:
    for root_name, kind in (("services", "service"), ("apps", "app")):
        root = ROOT / root_name
        if not root.is_dir():
            raise ValidationError(f"missing {root_name} directory")
        expected_names = {component.identifier for component in COMPONENTS if component.kind == kind}
        found_names = {entry.name for entry in root.iterdir() if entry.is_dir()}
        if found_names != expected_names:
            raise ValidationError(
                f"{root_name} inventory mismatch: expected {sorted(expected_names)}, found {sorted(found_names)}"
            )
        stray_files = sorted(entry.name for entry in root.iterdir() if entry.is_file())
        if stray_files:
            raise ValidationError(f"unexpected file at {root_name} boundary: {stray_files}")
    for component in COMPONENTS:
        validate_component(component)


def validate_ownership() -> None:
    ownership_file = ROOT / "docs" / "architecture" / "service-ownership.yaml"
    try:
        data = json.loads(ownership_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid service ownership document: {error}") from error
    expected_components = [
        {
            "id": component.identifier,
            "kind": component.kind,
            "path": component.path,
            "bounded_context": component.bounded_context,
            "status": component.status,
            "data_ownership": component.data_ownership,
            "allowed_workspace_dependencies": ALLOWED_DEPENDENCIES,
        }
        for component in COMPONENTS
    ]
    expected = {
        "format": "service-ownership-v1",
        "source": "docs/architecture/container-map.md",
        "components": expected_components,
    }
    if data != expected:
        raise ValidationError("service ownership metadata is not in exact parity with the skeleton inventory")


def validate_workspace() -> None:
    validate_component_inventory()
    validate_packages()
    validate_ownership()


def artifact_payload(component: Component, manifest: dict[str, Any]) -> bytes:
    directory = ROOT / component.path
    file_hashes = {
        name: sha256_bytes((directory / name).read_bytes()) for name in sorted(regular_relative_files(directory))
    }
    metadata = {
        "format": "skeleton-artifact-v1",
        "component": manifest,
        "local_files": file_hashes,
    }
    return json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def write_deterministic_zip(component: Component, output_dir: Path) -> Path:
    manifest = validate_component(component)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / manifest["build_artifact"]
    members = {
        name: (ROOT / component.path / name).read_bytes()
        for name in regular_relative_files(ROOT / component.path)
    }
    members["artifact-metadata.json"] = artifact_payload(component, manifest)
    try:
        with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name in sorted(members):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, members[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    except (OSError, zipfile.BadZipFile) as error:
        raise ValidationError(f"build failure for {component.path}: {error}") from error
    return artifact


def build_component(component_path: str, output_dir: Path) -> Path:
    component = component_by_path(component_path)
    validate_component(component)
    validate_generated_contracts()
    return write_deterministic_zip(component, output_dir)


def build_all(output_dir: Path) -> list[Path]:
    validate_workspace()
    return [write_deterministic_zip(component, output_dir) for component in COMPONENTS]


def run_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "tests/test_monorepo_skeleton.py"], cwd=ROOT, check=False
    )
    if result.returncode != 0:
        raise ValidationError(f"workspace unittest suite failed with exit code {result.returncode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("bootstrap")
    subcommands.add_parser("lint")
    subcommands.add_parser("test")
    build = subcommands.add_parser("build")
    build.add_argument("component")
    build.add_argument("--output-dir", type=Path, default=ROOT / "deploy" / "artifacts")
    for command in (subcommands.add_parser("build-all"), subcommands.add_parser("verify")):
        command.add_argument("--output-dir", type=Path, default=ROOT / "deploy" / "artifacts")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command in {"bootstrap", "lint"}:
            validate_workspace()
            print(f"{arguments.command}: workspace skeleton is valid")
        elif arguments.command == "test":
            validate_workspace()
            run_tests()
            print("test: workspace skeleton tests passed")
        elif arguments.command == "build":
            artifact = build_component(arguments.component, arguments.output_dir)
            print(artifact)
        elif arguments.command == "build-all":
            for artifact in build_all(arguments.output_dir):
                print(artifact)
        elif arguments.command == "verify":
            validate_workspace()
            run_tests()
            for artifact in build_all(arguments.output_dir):
                print(artifact)
            print("verify: workspace skeleton is valid and artifacts were built")
    except ValidationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
