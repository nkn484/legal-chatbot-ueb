"""Isolated governance lifecycle tests; never invoke the repository's live gate state."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]


class GateFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="prompt-gate-lifecycle-")
        self.root = Path(self.temp.name) / "repo"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "prompts").mkdir()
        (self.root / ".agent-run").mkdir()
        (self.root / "work").mkdir()
        (self.root / "docs").mkdir()
        shutil.copy2(SOURCE_ROOT / "scripts" / "prompt_gate.py", self.root / "scripts" / "prompt_gate.py")
        (self.root / "work" / "tracked.txt").write_text("original\n", encoding="utf-8")
        self.manifest = {
            "schema_version": 1,
            "prompts": {
                "A": self.item([], "one"),
                "B": self.item(["A"], "two"),
                "C": self.item(["B"], "three"),
            },
        }
        self.state = {"schema_version": 1, "prompts": {key: self.entry() for key in self.manifest["prompts"]}}
        self.write_manifest()
        self.write_state()
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Gate Test")
        self.git("add", ".")
        self.git("commit", "-m", "fixture")

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def item(dependencies: list[str], group: str) -> dict[str, object]:
        return {"dependencies": dependencies, "group": group, "write_roots": ["work/"],
                "preferred_agents": [], "required_report": "docs/report.md"}

    @staticmethod
    def entry(**changes: object) -> dict[str, object]:
        value: dict[str, object] = {"status": "NOT_STARTED", "started_at": None, "submitted_at": None,
                                    "human_approved_at": None, "human_approved_by": None,
                                    "approval_note": None, "report": None, "evidence": []}
        value.update(changes)
        return value

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True)

    def gate(self, *args: str, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if environment:
            env.update(environment)
        return subprocess.run([sys.executable, str(self.root / "scripts" / "prompt_gate.py"), *args],
                              cwd=self.root, text=True, capture_output=True, check=False, env=env)

    def write_manifest(self) -> None:
        (self.root / "prompts" / "manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def write_state(self) -> None:
        (self.root / ".agent-run" / "prompt-state.json").write_text(json.dumps(self.state), encoding="utf-8")

    def read_state(self) -> dict:
        return json.loads((self.root / ".agent-run" / "prompt-state.json").read_text(encoding="utf-8"))

    def make_pass(self, prompt_id: str) -> None:
        self.assertEqual(0, self.gate("start", prompt_id).returncode)
        report = self.root / "docs" / f"{prompt_id}.md"
        evidence = self.root / "docs" / f"{prompt_id}.txt"
        report.write_text("Trạng thái\nĐã thay đổi\nBằng chứng\nSai lệch\nĐề xuất prompt tiếp theo\n", encoding="utf-8")
        evidence.write_text("evidence\n", encoding="utf-8")
        self.assertEqual(0, self.gate("submit", prompt_id, "--report", f"docs/{prompt_id}.md",
                                    "--evidence", f"docs/{prompt_id}.txt").returncode)
        self.assertEqual(0, self.gate("approve", prompt_id, "--by", "USER", "--note", "approved").returncode)


class CancelStartTests(GateFixture):
    def test_cancel_pristine_preserves_started_at_and_files(self) -> None:
        self.assertEqual(0, self.gate("start", "A").returncode)
        before = self.read_state()["prompts"]["A"]
        result = self.gate("cancel-start", "A", "--by", "USER", "--note", "mistake")
        self.assertEqual(0, result.returncode, result.stderr)
        after = self.read_state()["prompts"]["A"]
        self.assertEqual("NOT_STARTED", after["status"])
        self.assertEqual(before["started_at"], after["history"][-1]["previous_started_at"])
        self.assertTrue((self.root / "work" / "tracked.txt").exists())
        self.assertEqual("original\n", (self.root / "work" / "tracked.txt").read_text(encoding="utf-8"))

    def test_cancel_refuses_submitted_or_awaiting_without_mutation(self) -> None:
        for entry in (
            self.entry(status="AWAITING_APPROVAL", submitted_at="time", report="docs/r.md", evidence=["docs/e"]),
            self.entry(status="IN_PROGRESS", submitted_at="time"),
            self.entry(status="IN_PROGRESS", report="docs/r.md"),
            self.entry(status="IN_PROGRESS", evidence=["docs/e"]),
        ):
            self.state["prompts"]["A"] = entry
            self.write_state()
            before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
            result = self.gate("cancel-start", "A", "--by", "USER", "--note", "no")
            self.assertEqual(2, result.returncode)
            self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())

    def test_cancel_refuses_created_modified_or_deleted_artifacts_only_in_root(self) -> None:
        for operation in ("created", "modified", "deleted"):
            with self.subTest(operation=operation):
                self.git("checkout", "--", "work")
                new_file = self.root / "work" / "new.txt"
                if new_file.exists():
                    new_file.unlink()
                self.state["prompts"]["A"] = self.entry()
                self.write_state()
                self.assertEqual(0, self.gate("start", "A").returncode)
                tracked = self.root / "work" / "tracked.txt"
                if operation == "created":
                    new_file.write_text("new", encoding="utf-8")
                elif operation == "modified":
                    tracked.write_text("changed", encoding="utf-8")
                else:
                    tracked.unlink()
                self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", operation).returncode)
        self.git("checkout", "--", "work")
        new_file = self.root / "work" / "new.txt"
        if new_file.exists():
            new_file.unlink()
        self.state["prompts"]["A"] = self.entry()
        self.write_state()
        self.assertEqual(0, self.gate("start", "A").returncode)
        (self.root / "outside.txt").write_text("unrelated", encoding="utf-8")
        self.assertEqual(0, self.gate("cancel-start", "A", "--by", "USER", "--note", "outside").returncode)
        self.assertTrue((self.root / "outside.txt").exists())

    def test_legacy_snapshot_uses_clean_git_fallback_and_rejects_dirty_root(self) -> None:
        self.state["prompts"]["A"] = self.entry(status="IN_PROGRESS", started_at="old")
        self.write_state()
        self.assertEqual(0, self.gate("cancel-start", "A", "--by", "USER", "--note", "legacy").returncode)
        self.state["prompts"]["A"] = self.entry(status="IN_PROGRESS", started_at="old")
        self.write_state()
        (self.root / "work" / "tracked.txt").write_text("dirty", encoding="utf-8")
        self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", "legacy").returncode)

    def test_snapshot_roots_missing_file_overlap_and_repo_root(self) -> None:
        self.manifest["prompts"]["A"]["write_roots"] = ["work/", "work/tracked.txt", "missing/", "."]
        self.write_manifest()
        self.assertEqual(0, self.gate("start", "A").returncode)
        snapshot = self.read_state()["prompts"]["A"]["start_snapshot"]["files"]
        self.assertEqual(1, list(snapshot).count("work/tracked.txt"))
        self.assertNotIn(".git/HEAD", snapshot)
        self.assertEqual(0, self.gate("cancel-start", "A", "--by", "USER", "--note", "clean").returncode)
        self.state = self.read_state()
        self.state["prompts"]["A"] = self.entry()
        self.write_state()
        self.assertEqual(0, self.gate("start", "A").returncode)
        (self.root / "missing").mkdir()
        self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", "created").returncode)

    def test_missing_root_symlink_and_invalid_roots_fail_closed(self) -> None:
        invalid_roots = [
            "../escape", str(self.root), "link-root", ".git", "nested/.git",
            ".GIT", ".git.", ".git ", "nested/.GIT", "nested/.git.",
        ]
        outside = self.root.parent / "outside"
        outside.mkdir(exist_ok=True)
        (self.root / "link-root").symlink_to(outside, target_is_directory=True)
        for root in invalid_roots:
            with self.subTest(root=root):
                self.manifest["prompts"]["A"]["write_roots"] = [root]
                self.write_manifest()
                before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
                self.assertEqual(2, self.gate("start", "A").returncode)
                self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())
        self.manifest["prompts"]["A"]["write_roots"] = ["later/"]
        self.write_manifest()
        self.assertEqual(0, self.gate("start", "A").returncode)
        (self.root / "later").symlink_to(outside, target_is_directory=True)
        self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", "symlink").returncode)

    def test_git_fallback_fails_closed_when_git_unavailable(self) -> None:
        self.state["prompts"]["A"] = self.entry(status="IN_PROGRESS", started_at="old")
        self.write_state()
        before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
        self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", "legacy",
                                      environment={"PATH": ""}).returncode)
        self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())

    def test_legacy_files_only_snapshot_uses_git_fallback(self) -> None:
        legacy = {"version": 1, "started_at": "old", "files": {"work/tracked.txt": "obsolete"}}
        self.state["prompts"]["A"] = self.entry(status="IN_PROGRESS", started_at="old", start_snapshot=legacy)
        self.write_state()
        self.assertEqual(0, self.gate("cancel-start", "A", "--by", "USER", "--note", "legacy").returncode)
        after = self.read_state()["prompts"]["A"]
        self.assertEqual("legacy_snapshot_git_fallback", after["history"][-1]["snapshot_mode"])
        self.assertEqual("old", after["history"][-1]["previous_started_at"])
        for mode in ("dirty", "unavailable"):
            with self.subTest(mode=mode):
                self.git("checkout", "--", "work")
                self.state["prompts"]["A"] = self.entry(status="IN_PROGRESS", started_at="old", start_snapshot=legacy)
                self.write_state()
                environment = None
                if mode == "dirty":
                    (self.root / "work" / "tracked.txt").write_text("dirty", encoding="utf-8")
                else:
                    environment = {"PATH": ""}
                before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
                self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", mode,
                                              environment=environment).returncode)
                self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())

    def test_direct_file_root_detects_modification_and_deletion(self) -> None:
        self.manifest["prompts"]["A"]["write_roots"] = ["work/tracked.txt"]
        self.write_manifest()
        for operation in ("modified", "deleted"):
            with self.subTest(operation=operation):
                self.git("checkout", "--", "work")
                self.state["prompts"]["A"] = self.entry()
                self.write_state()
                self.assertEqual(0, self.gate("start", "A").returncode)
                target = self.root / "work" / "tracked.txt"
                if operation == "modified":
                    target.write_text("changed", encoding="utf-8")
                else:
                    target.unlink()
                self.assertEqual(2, self.gate("cancel-start", "A", "--by", "USER", "--note", operation).returncode)
        self.git("checkout", "--", "work")
        self.state["prompts"]["A"] = self.entry()
        self.write_state()
        self.assertEqual(0, self.gate("start", "A").returncode)
        self.assertEqual(0, self.gate("cancel-start", "A", "--by", "USER", "--note", "unchanged").returncode)


class ReopenTests(GateFixture):
    def test_reopen_pass_archives_approval_and_resets_target(self) -> None:
        self.make_pass("A")
        result = self.gate("reopen", "A", "--by", "USER", "--note", "correct")
        self.assertEqual(0, result.returncode, result.stderr)
        entry = self.read_state()["prompts"]["A"]
        self.assertEqual(("IN_PROGRESS", 2, None, None, []),
                         (entry["status"], entry["revision"], entry["human_approved_at"], entry["report"], entry["evidence"]))
        self.assertEqual("APPROVAL_ARCHIVED", entry["approval_history"][-1]["action"])
        self.assertEqual(Path("docs") / "A.md", Path(entry["history"][-1]["prior_approval"]["report"]))
        self.assertEqual(["B", "C"], entry["history"][-1]["descendants_checked"])

    def test_reopen_refuses_nonpristine_descendants(self) -> None:
        self.make_pass("A")
        for descendant_id, child in (
            ("B", self.entry(status="AWAITING_APPROVAL")), ("C", self.entry(status="PASS")),
            ("B", self.entry(status="DEFERRED")), ("C", self.entry(status="FAIL")),
            ("B", self.entry(status="BLOCKED")), ("C", self.entry(status="UNKNOWN")),
            ("C", self.entry(report="docs/r")),
            ("B", self.entry(evidence=["docs/e"])), ("C", self.entry(submitted_at="time")),
        ):
            self.state = self.read_state()
            self.state["prompts"]["B"] = self.entry()
            self.state["prompts"]["C"] = self.entry()
            self.state["prompts"][descendant_id] = child
            self.write_state()
            before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
            self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "no").returncode)
            self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())

    def test_in_progress_descendant_requires_cancel_then_reopen_succeeds(self) -> None:
        self.make_pass("A")
        self.assertEqual(0, self.gate("start", "B").returncode)
        self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "fix").returncode)
        self.assertEqual(0, self.gate("cancel-start", "B", "--by", "USER", "--note", "stop").returncode)
        self.assertEqual(0, self.gate("reopen", "A", "--by", "USER", "--note", "fix").returncode)

    def test_reopened_parent_blocks_all_successors_until_each_new_approval(self) -> None:
        self.make_pass("A")
        self.assertEqual(0, self.gate("reopen", "A", "--by", "USER", "--note", "fix").returncode)
        blocked = self.gate("check", "B")
        self.assertEqual(2, blocked.returncode)
        self.assertIn("status IN_PROGRESS", blocked.stderr)
        self.assertEqual(2, self.gate("check", "C").returncode)
        self.assertEqual(2, self.gate("start", "C").returncode)
        self.make_pass("A")
        approved = self.read_state()["prompts"]["A"]
        self.assertEqual(2, approved["approved_revision"])
        self.assertEqual(0, self.gate("check", "B").returncode)
        self.assertEqual(2, self.gate("check", "C").returncode)
        self.make_pass("B")
        self.assertEqual(0, self.gate("check", "C").returncode)

    def test_reopen_requires_current_approval_revision(self) -> None:
        self.state["prompts"]["A"] = self.entry(status="PASS", human_approved_at="time", human_approved_by="U",
                                                   approval_note="ok", revision=2, approved_revision=1)
        self.write_state()
        before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
        self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "no").returncode)
        self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())
        self.state["prompts"]["A"].pop("approved_revision")
        self.write_state()
        before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
        self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "no").returncode)
        self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())

    def test_unknown_target_status_reopen_does_not_mutate(self) -> None:
        self.state["prompts"]["A"] = self.entry(status="UNKNOWN")
        self.write_state()
        before = (self.root / ".agent-run" / "prompt-state.json").read_bytes()
        self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "no").returncode)
        self.assertEqual(before, (self.root / ".agent-run" / "prompt-state.json").read_bytes())

    def test_unknown_and_cyclic_graph_fail_closed(self) -> None:
        self.manifest["prompts"]["B"]["dependencies"] = ["MISSING"]
        self.write_manifest()
        self.assertEqual(2, self.gate("check", "B").returncode)
        self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "no").returncode)
        self.manifest["prompts"]["B"]["dependencies"] = ["C"]
        self.manifest["prompts"]["C"]["dependencies"] = ["B"]
        self.write_manifest()
        self.assertEqual(2, self.gate("check", "B").returncode)
        self.assertEqual(2, self.gate("reopen", "A", "--by", "USER", "--note", "no").returncode)

    def test_human_commands_reject_empty_metadata(self) -> None:
        self.make_pass("A")
        for command in (("reopen", "A"), ("cancel-start", "B")):
            result = self.gate(*command, "--by", " ", "--note", " ")
            self.assertEqual(2, result.returncode)


if __name__ == "__main__":
    unittest.main()
