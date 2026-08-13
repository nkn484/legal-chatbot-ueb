#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


required = [
    ROOT / "AGENTS.md",
    ROOT / "opencode.jsonc",
    ROOT / ".opencode" / "oh-my-opencode-slim.jsonc",
    ROOT / "prompts" / "00_HARD_RULES.md",
    ROOT / "prompts" / "manifest.json",
    ROOT / ".agent-run" / "prompt-state.json",
    ROOT / "scripts" / "prompt_gate.py",
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
    prompt_id = match.group(1)
    for marker in ("agent: orchestrator", "prompt_gate.py start", "prompt_gate.py submit", "AWAITING_APPROVAL"):
        if marker not in text:
            fail(f"{path.name} missing marker {marker}")
    if prompt_id not in manifest["prompts"]:
        fail(f"{path.name} has unknown ID {prompt_id}")

for config in (ROOT / "opencode.jsonc", ROOT / ".opencode" / "oh-my-opencode-slim.jsonc"):
    json.loads(config.read_text(encoding="utf-8"))

result = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "prompt_gate.py"), "check", "01.1"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)
if result.returncode != 0 or "ELIGIBLE 01.1" not in result.stdout:
    fail("initial gate 01.1 is not eligible")

with tempfile.TemporaryDirectory(prefix="chatbot-prompt-gate-") as temporary:
    test_root = Path(temporary) / "repo"
    shutil.copytree(ROOT, test_root)
    gate = test_root / "scripts" / "prompt_gate.py"

    def run_gate(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(gate), *arguments],
            cwd=test_root,
            text=True,
            capture_output=True,
            check=False,
        )

    if run_gate("start", "01.1").returncode != 0:
        fail("lifecycle: cannot start 01.1")
    report = test_root / "docs" / "progress" / "01.1.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Test\n\n## Trạng thái\nPASS_CANDIDATE\n\n## Đã thay đổi\nfixture\n\n"
        "## Bằng chứng\nfixture\n\n## Sai lệch\nnone\n\n## Đề xuất prompt tiếp theo\n01.2\n",
        encoding="utf-8",
    )
    evidence = test_root / "docs" / "repository-inventory.md"
    evidence.write_text("fixture\n", encoding="utf-8")
    submitted = run_gate(
        "submit",
        "01.1",
        "--report",
        "docs/progress/01.1.md",
        "--evidence",
        "docs/repository-inventory.md",
    )
    if submitted.returncode != 0 or "AWAITING_APPROVAL" not in submitted.stdout:
        fail("lifecycle: cannot submit 01.1")
    if run_gate("check", "01.2").returncode == 0:
        fail("lifecycle: 01.2 opened before human approval")
    approved = run_gate("approve", "01.1", "--by", "TEST_USER", "--note", "test approval")
    if approved.returncode != 0 or "PASS 01.1" not in approved.stdout:
        fail("lifecycle: cannot approve 01.1")
    if run_gate("check", "01.2").returncode != 0:
        fail("lifecycle: 01.2 did not open after approval")

print("PASS: 72 commands, configs, manifest, state and full gate lifecycle are valid")
