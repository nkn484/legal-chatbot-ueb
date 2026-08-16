"""Regression coverage for the Prompt 03.1 repository/build boundary skeleton."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "packages" / "workspace-tooling" / "workspace.py"
SERVICES = (
    "api-gateway",
    "identity-service",
    "audit-service",
    "document-service",
    "processing-service",
    "index-service",
    "retrieval-service",
    "citation-service",
    "chat-service",
    "provider-service",
    "feedback-service",
    "evaluation-service",
)
APPS = ("web-chat", "admin-portal")
COMPONENTS = tuple(("services", identifier) for identifier in SERVICES) + tuple(
    ("apps", identifier) for identifier in APPS
)
ALLOWED_DEPENDENCIES = ["packages/generated-contracts"]


def run_tool(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def tree_digest(root: Path) -> tuple[int, str]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rows.append(
                (path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())
            )
    encoded = "".join(f"{name}\0{digest}\n" for name, digest in rows).encode("utf-8")
    return len(rows), hashlib.sha256(encoded).hexdigest()


class MonorepoSkeletonTests(unittest.TestCase):
    def test_exact_inventory_and_local_manifests(self) -> None:
        self.assertEqual({entry.name for entry in (ROOT / "services").iterdir() if entry.is_dir()}, set(SERVICES))
        self.assertEqual({entry.name for entry in (ROOT / "apps").iterdir() if entry.is_dir()}, set(APPS))
        for root_name, identifier in COMPONENTS:
            component = ROOT / root_name / identifier
            self.assertEqual(
                {path.relative_to(component).as_posix() for path in component.rglob("*") if path.is_file()},
                {"README.md", "component.toml"},
            )
            manifest = tomllib.loads((component / "component.toml").read_text(encoding="utf-8"))["component"]
            self.assertEqual(manifest["id"], identifier)
            self.assertEqual(manifest["kind"], "service" if root_name == "services" else "app")
            self.assertEqual(manifest["path"], f"{root_name}/{identifier}")
            self.assertEqual(manifest["build_artifact"], f"{identifier}-skeleton.zip")
            self.assertEqual(manifest["allowed_workspace_dependencies"], ALLOWED_DEPENDENCIES)
        self.assertEqual(
            {identifier for identifier in SERVICES if tomllib.loads((ROOT / "services" / identifier / "component.toml").read_text(encoding="utf-8"))["component"]["status"] == "CORE"},
            set(SERVICES) - {"provider-service", "feedback-service", "evaluation-service"},
        )

    def test_each_component_builds_independently_and_artifacts_are_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary)
            for root_name, identifier in COMPONENTS:
                output_dir = output_root / identifier
                result = run_tool("build", f"{root_name}/{identifier}", "--output-dir", str(output_dir))
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                artifact = output_dir / f"{identifier}-skeleton.zip"
                self.assertTrue(artifact.is_file())
                with zipfile.ZipFile(artifact) as archive:
                    self.assertEqual(archive.namelist(), ["README.md", "artifact-metadata.json", "component.toml"])
                    metadata = json.loads(archive.read("artifact-metadata.json"))
                    self.assertEqual(metadata["component"]["id"], identifier)
                    self.assertEqual(metadata["component"]["path"], f"{root_name}/{identifier}")
                    self.assertEqual(set(metadata["local_files"]), {"README.md", "component.toml"})
                    self.assertNotIn("services/", "\n".join(archive.namelist()))
                    self.assertNotIn("apps/", "\n".join(archive.namelist()))

    def test_targeted_build_succeeds_in_isolated_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            isolated_root = Path(temporary)

            def copy_files(source: Path, destination: Path) -> None:
                for source_path in source.rglob("*"):
                    if source_path.is_file():
                        target_path = destination / source_path.relative_to(source)
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        target_path.write_bytes(source_path.read_bytes())

            copy_files(ROOT / "contracts", isolated_root / "contracts")
            copy_files(
                ROOT / "packages" / "generated-contracts",
                isolated_root / "packages" / "generated-contracts",
            )
            copy_files(
                ROOT / "packages" / "workspace-tooling",
                isolated_root / "packages" / "workspace-tooling",
            )
            copy_files(ROOT / "services" / "api-gateway", isolated_root / "services" / "api-gateway")

            self.assertFalse((isolated_root / "apps").exists())
            self.assertFalse((isolated_root / "services" / "identity-service").exists())
            self.assertFalse((isolated_root / "docs" / "architecture" / "service-ownership.yaml").exists())

            output_dir = isolated_root / "artifacts"
            result = subprocess.run(
                [
                    sys.executable,
                    str(isolated_root / "packages" / "workspace-tooling" / "workspace.py"),
                    "build",
                    "services/api-gateway",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=isolated_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            artifact = output_dir / "api-gateway-skeleton.zip"
            self.assertTrue(artifact.is_file())
            with zipfile.ZipFile(artifact) as archive:
                self.assertEqual(archive.namelist(), ["README.md", "artifact-metadata.json", "component.toml"])
                metadata = json.loads(archive.read("artifact-metadata.json"))
                self.assertEqual(metadata["component"]["id"], "api-gateway")
                self.assertEqual(metadata["component"]["path"], "services/api-gateway")

    def test_artifact_bytes_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            first = temporary_root / "first"
            second = temporary_root / "second"
            for output in (first, second):
                result = run_tool("build", "services/api-gateway", "--output-dir", str(output))
                self.assertEqual(result.returncode, 0, msg=result.stderr)
            first_bytes = (first / "api-gateway-skeleton.zip").read_bytes()
            second_bytes = (second / "api-gateway-skeleton.zip").read_bytes()
            self.assertEqual(hashlib.sha256(first_bytes).digest(), hashlib.sha256(second_bytes).digest())

    def test_ownership_parity_and_generated_contract_integrity(self) -> None:
        ownership = json.loads((ROOT / "docs" / "architecture" / "service-ownership.yaml").read_text(encoding="utf-8"))
        entries = ownership["components"]
        self.assertEqual([(entry["kind"], entry["id"]) for entry in entries], [("service", item) for item in SERVICES] + [("app", item) for item in APPS])
        for entry in entries:
            self.assertEqual(entry["allowed_workspace_dependencies"], ALLOWED_DEPENDENCIES)
            self.assertTrue(entry["data_ownership"].startswith("Self-only"))
            manifest = tomllib.loads((ROOT / entry["path"] / "component.toml").read_text(encoding="utf-8"))["component"]
            self.assertEqual(entry["status"], manifest["status"])
            self.assertEqual(entry["path"], manifest["path"])
        index = json.loads((ROOT / "packages" / "generated-contracts" / "contracts-index.json").read_text(encoding="utf-8"))
        count, digest = tree_digest(ROOT / "contracts")
        self.assertEqual(index["source_root"], "contracts")
        self.assertEqual(index["source_file_count"], count)
        self.assertEqual(index["source_tree_sha256"], digest)

    def test_lint_proves_no_shared_business_or_runtime_package(self) -> None:
        result = run_tool("lint")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        packages = {entry.name for entry in (ROOT / "packages").iterdir() if entry.is_dir()}
        self.assertEqual(packages, {"generated-contracts", "workspace-tooling"})
        generated_files = {
            path.relative_to(ROOT / "packages" / "generated-contracts").as_posix()
            for path in (ROOT / "packages" / "generated-contracts").rglob("*")
            if path.is_file()
        }
        self.assertEqual(generated_files, {"README.md", "package.toml", "contracts-index.json"})


if __name__ == "__main__":
    unittest.main()
