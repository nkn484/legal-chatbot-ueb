#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> NoReturn:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


required = [
    ROOT / "AGENTS.md", ROOT / "opencode.jsonc", ROOT / ".opencode" / "oh-my-opencode-slim.jsonc",
    ROOT / "prompts" / "00_HARD_RULES.md", ROOT / "prompts" / "manifest.json",
    ROOT / ".agent-run" / "prompt-state.json", ROOT / "scripts" / "prompt_gate.py",
    ROOT / "docs" / "prompt-transition-rules.md", ROOT / "tests" / "test_prompt_gate_lifecycle.py",
]
for path in required:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")

manifest = json.loads((ROOT / "prompts" / "manifest.json").read_text(encoding="utf-8"))
state = json.loads((ROOT / ".agent-run" / "prompt-state.json").read_text(encoding="utf-8"))
commands = sorted((ROOT / ".opencode" / "commands").glob("prompt-[0-9][0-9]-[0-9]*.md"))
if len(commands) != 72:
    fail(f"expected 72 prompt commands, got {len(commands)}")
if len(manifest["prompts"]) != 72 or len(state["prompts"]) != 72:
    fail("manifest/state prompt count is not 72")
for path in commands:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"invalid frontmatter start in {path.name}")
    match = re.search(r"Prompt ID: `(\d{2}\.\d+)`", text)
    if not match:
        fail(f"missing Prompt ID in {path.name}")
    for marker in ("agent: orchestrator", "prompt_gate.py start", "prompt_gate.py submit", "AWAITING_APPROVAL"):
        if marker not in text:
            fail(f"{path.name} missing marker {marker}")
    if match.group(1) not in manifest["prompts"]:
        fail(f"{path.name} has unknown ID {match.group(1)}")
for config in (ROOT / "opencode.jsonc", ROOT / ".opencode" / "oh-my-opencode-slim.jsonc"):
    json.loads(config.read_text(encoding="utf-8"))

help_result = subprocess.run([sys.executable, str(ROOT / "scripts" / "prompt_gate.py"), "--help"], cwd=ROOT,
                             text=True, capture_output=True, check=False)
if help_result.returncode != 0 or "cancel-start" not in help_result.stdout or "reopen" not in help_result.stdout:
    fail("prompt gate help does not expose revision governance commands")
gate_source = (ROOT / "scripts" / "prompt_gate.py").read_text(encoding="utf-8")
for marker in ("rejection_history", "REJECTION_ARCHIVED_LEGACY"):
    if marker not in gate_source:
        fail(f"prompt gate missing rejection governance marker {marker}")
rules = (ROOT / "docs" / "prompt-transition-rules.md").read_text(encoding="utf-8")
for marker in ("cancel-start", "reopen", "approved_revision", "start_snapshot", "rejection_history",
               "REJECTION_ARCHIVED_LEGACY", "Reopen từ PASS", "Reopen từ FAIL"):
    if marker not in rules:
        fail(f"transition rules missing governance marker {marker}")

# The unittest fixture copies the gate into a new temporary repository, initializes Git there,
# and creates fresh NOT_STARTED state. It never invokes governance commands against ROOT.
result = subprocess.run([sys.executable, "-m", "unittest", "tests.test_prompt_gate_lifecycle", "-v"], cwd=ROOT,
                        text=True, capture_output=True, check=False)
if result.returncode != 0:
    fail("governance lifecycle tests failed:\n" + result.stdout + result.stderr)

with tempfile.TemporaryDirectory(prefix="prompt-gate-verify-") as temporary:
    test_root = Path(temporary) / "repo"
    (test_root / "scripts").mkdir(parents=True)
    (test_root / "prompts").mkdir()
    (test_root / ".agent-run").mkdir()
    (test_root / "work").mkdir()
    (test_root / "docs").mkdir()
    shutil.copy2(ROOT / "scripts" / "prompt_gate.py", test_root / "scripts" / "prompt_gate.py")
    compact_manifest = {"schema_version": 1, "prompts": {
        "01.1": {"dependencies": [], "group": "01", "write_roots": ["work/"],
                   "preferred_agents": [], "required_report": "docs/report.md"},
        "01.2": {"dependencies": ["01.1"], "group": "01", "write_roots": ["work/"],
                   "preferred_agents": [], "required_report": "docs/report.md"},
    }}
    fresh_state = {"schema_version": 1, "prompts": {
        prompt_id: {"status": "NOT_STARTED", "started_at": None, "submitted_at": None,
                    "human_approved_at": None, "human_approved_by": None, "approval_note": None,
                    "report": None, "evidence": []}
        for prompt_id in compact_manifest["prompts"]
    }}
    (test_root / "prompts" / "manifest.json").write_text(json.dumps(compact_manifest), encoding="utf-8")
    (test_root / ".agent-run" / "prompt-state.json").write_text(json.dumps(fresh_state), encoding="utf-8")

    def gate(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(test_root / "scripts" / "prompt_gate.py"), *arguments],
                              cwd=test_root, text=True, capture_output=True, check=False)

    if gate("start", "01.1").returncode != 0:
        fail("isolated lifecycle: cannot start predecessor")
    report = test_root / "docs" / "report.md"
    evidence = test_root / "docs" / "evidence.txt"
    report.write_text("Trạng thái\nĐã thay đổi\nBằng chứng\nSai lệch\nĐề xuất prompt tiếp theo\n", encoding="utf-8")
    evidence.write_text("fixture\n", encoding="utf-8")
    if gate("submit", "01.1", "--report", "docs/report.md", "--evidence", "docs/evidence.txt").returncode != 0:
        fail("isolated lifecycle: cannot submit predecessor")
    if gate("check", "01.2").returncode == 0:
        fail("isolated lifecycle: successor opened before approval")
    if gate("approve", "01.1", "--by", "TEST_USER", "--note", "fixture approval").returncode != 0:
        fail("isolated lifecycle: cannot approve predecessor")
    if gate("check", "01.2").returncode != 0:
        fail("isolated lifecycle: successor remained blocked after approval")

print("PASS: 72 commands, configs, manifest/state structure, and revision governance lifecycle are valid")
