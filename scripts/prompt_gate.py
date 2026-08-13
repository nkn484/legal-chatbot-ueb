#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "prompts" / "manifest.json"
STATE_PATH = ROOT / ".agent-run" / "prompt-state.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read valid JSON: {path}: {exc}") from exc


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(STATE_PATH)


def get_prompt(manifest: dict[str, Any], prompt_id: str) -> dict[str, Any]:
    try:
        return manifest["prompts"][prompt_id]
    except KeyError as exc:
        raise SystemExit(f"Unknown prompt ID: {prompt_id}") from exc


def eligible(manifest: dict[str, Any], state: dict[str, Any], prompt_id: str) -> tuple[bool, list[str]]:
    item = get_prompt(manifest, prompt_id)
    reasons: list[str] = []
    for dependency in item.get("dependencies", []):
        dep_state = state["prompts"][dependency]
        if dep_state["status"] not in {"PASS", "DEFERRED"} or not dep_state.get("human_approved_at"):
            reasons.append(f"dependency {dependency} is not human-approved PASS/DEFERRED")
    current = state["prompts"][prompt_id]["status"]
    if current not in {"NOT_STARTED", "BLOCKED", "IN_PROGRESS"}:
        reasons.append(f"current status {current} cannot be started/resumed")
    return not reasons, reasons


def command_context(args: argparse.Namespace) -> int:
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    item = get_prompt(manifest, args.prompt_id)
    ok, reasons = eligible(manifest, state, args.prompt_id)
    print(json.dumps({
        "prompt_id": args.prompt_id,
        "eligible": ok,
        "reasons": reasons,
        "status": state["prompts"][args.prompt_id]["status"],
        "dependencies": item.get("dependencies", []),
        "write_roots": item["write_roots"],
        "preferred_agents": item["preferred_agents"],
        "required_report": item["required_report"],
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def command_check(args: argparse.Namespace) -> int:
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    ok, reasons = eligible(manifest, state, args.prompt_id)
    if ok:
        print(f"ELIGIBLE {args.prompt_id}")
        return 0
    print(f"BLOCKED {args.prompt_id}: " + "; ".join(reasons), file=sys.stderr)
    return 2


def command_start(args: argparse.Namespace) -> int:
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    ok, reasons = eligible(manifest, state, args.prompt_id)
    if not ok:
        print("; ".join(reasons), file=sys.stderr)
        return 2
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "IN_PROGRESS":
        entry.update({"status": "IN_PROGRESS", "started_at": now(), "submitted_at": None})
        save_state(state)
    print(f"IN_PROGRESS {args.prompt_id}")
    return 0


def resolve_repo_path(raw: str) -> Path:
    path = (ROOT / raw).resolve()
    if ROOT not in path.parents and path != ROOT:
        raise SystemExit(f"Evidence escapes repository: {raw}")
    return path


def command_submit(args: argparse.Namespace) -> int:
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    get_prompt(manifest, args.prompt_id)
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "IN_PROGRESS":
        print(f"Prompt must be IN_PROGRESS, got {entry['status']}", file=sys.stderr)
        return 2
    report = resolve_repo_path(args.report)
    evidence = [resolve_repo_path(value) for value in args.evidence]
    missing = [str(path.relative_to(ROOT)) for path in [report, *evidence] if not path.exists()]
    if missing:
        print("Missing report/evidence: " + ", ".join(missing), file=sys.stderr)
        return 2
    if not evidence:
        print("At least one evidence path is required", file=sys.stderr)
        return 2
    report_text = report.read_text(encoding="utf-8", errors="replace")
    required_markers = ["Trạng thái", "Đã thay đổi", "Bằng chứng", "Sai lệch", "Đề xuất prompt tiếp theo"]
    absent = [marker for marker in required_markers if marker not in report_text]
    if absent:
        print("Report missing sections: " + ", ".join(absent), file=sys.stderr)
        return 2
    entry.update({
        "status": "AWAITING_APPROVAL",
        "submitted_at": now(),
        "report": str(report.relative_to(ROOT)),
        "evidence": [str(path.relative_to(ROOT)) for path in evidence],
    })
    save_state(state)
    print(f"AWAITING_APPROVAL {args.prompt_id}")
    return 0


def require_human_metadata(args: argparse.Namespace) -> None:
    if not args.by.strip() or not args.note.strip():
        raise SystemExit("--by and non-empty --note are required")


def command_approve(args: argparse.Namespace) -> int:
    require_human_metadata(args)
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    get_prompt(manifest, args.prompt_id)
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "AWAITING_APPROVAL":
        print(f"Prompt must be AWAITING_APPROVAL, got {entry['status']}", file=sys.stderr)
        return 2
    entry.update({
        "status": "PASS",
        "human_approved_at": now(),
        "human_approved_by": args.by,
        "approval_note": args.note,
    })
    save_state(state)
    print(f"PASS {args.prompt_id}")
    return 0


def command_reject(args: argparse.Namespace) -> int:
    require_human_metadata(args)
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    get_prompt(manifest, args.prompt_id)
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "AWAITING_APPROVAL":
        print(f"Prompt must be AWAITING_APPROVAL, got {entry['status']}", file=sys.stderr)
        return 2
    entry.update({
        "status": "FAIL",
        "human_approved_at": now(),
        "human_approved_by": args.by,
        "approval_note": args.note,
    })
    save_state(state)
    print(f"FAIL {args.prompt_id}")
    return 0


def command_defer_group(args: argparse.Namespace) -> int:
    require_human_metadata(args)
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    targets = [prompt_id for prompt_id, item in manifest["prompts"].items() if item["group"] == args.group]
    if not targets:
        raise SystemExit(f"Unknown group: {args.group}")
    first_item = manifest["prompts"][targets[0]]
    for dependency in first_item.get("dependencies", []):
        dep_state = state["prompts"][dependency]
        if dep_state["status"] not in {"PASS", "DEFERRED"} or not dep_state.get("human_approved_at"):
            raise SystemExit(f"Cannot defer group {args.group}: dependency {dependency} is not approved")
    for prompt_id in targets:
        entry = state["prompts"][prompt_id]
        if entry["status"] != "NOT_STARTED":
            raise SystemExit(f"Cannot defer {prompt_id}: status is {entry['status']}")
    stamp = now()
    for prompt_id in targets:
        state["prompts"][prompt_id].update({
            "status": "DEFERRED",
            "human_approved_at": stamp,
            "human_approved_by": args.by,
            "approval_note": args.note,
        })
    save_state(state)
    print(f"DEFERRED group {args.group}: {len(targets)} prompts")
    return 0


def command_status(args: argparse.Namespace) -> int:
    state = load(STATE_PATH)
    counts: dict[str, int] = {}
    for prompt_id, entry in state["prompts"].items():
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        if args.all or entry["status"] != "NOT_STARTED":
            print(f"{prompt_id}\t{entry['status']}")
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prompt gate for Chatbot Phap luat")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("context", command_context), ("check", command_check), ("start", command_start)):
        child = sub.add_parser(name)
        child.add_argument("prompt_id")
        child.set_defaults(func=func)
    submit = sub.add_parser("submit")
    submit.add_argument("prompt_id")
    submit.add_argument("--report", required=True)
    submit.add_argument("--evidence", action="append", default=[], required=True)
    submit.set_defaults(func=command_submit)
    for name, func in (("approve", command_approve), ("reject", command_reject)):
        child = sub.add_parser(name)
        child.add_argument("prompt_id")
        child.add_argument("--by", required=True)
        child.add_argument("--note", required=True)
        child.set_defaults(func=func)
    defer = sub.add_parser("defer-group")
    defer.add_argument("group")
    defer.add_argument("--by", required=True)
    defer.add_argument("--note", required=True)
    defer.set_defaults(func=command_defer_group)
    status = sub.add_parser("status")
    status.add_argument("--all", action="store_true")
    status.set_defaults(func=command_status)
    return parser


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    raise SystemExit(parsed.func(parsed))
