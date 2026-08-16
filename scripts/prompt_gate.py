#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "prompts" / "manifest.json"
STATE_PATH = ROOT / ".agent-run" / "prompt-state.json"
IGNORED_SNAPSHOT_NAMES = {".git", "__pycache__", ".DS_Store"}


class WriteRootError(ValueError):
    """A manifest write root cannot safely be used for artifact detection."""


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


def entry_revision(entry: dict[str, Any]) -> int:
    """Read legacy entries as revision one without rewriting state."""
    return entry.get("revision", 1)


def effective_approved_revision(entry: dict[str, Any]) -> int | None:
    """Return an approval only when its status is an effective approval state."""
    if entry.get("status") not in {"PASS", "DEFERRED"}:
        return None
    if "approved_revision" in entry:
        return entry["approved_revision"]
    if entry.get("human_approved_at"):
        return 1
    return None


def history(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return list(entry.get("history", []))


def approval_history(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return list(entry.get("approval_history", []))


def rejection_history(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return list(entry.get("rejection_history", []))


def has_current_approval(entry: dict[str, Any]) -> bool:
    return any(entry.get(key) is not None for key in (
        "human_approved_at", "human_approved_by", "approval_note", "approved_revision",
    ))


def dependency_graph_error(manifest: dict[str, Any]) -> str | None:
    prompts = manifest.get("prompts", {})
    for prompt_id, item in prompts.items():
        for dependency in item.get("dependencies", []):
            if dependency not in prompts:
                return f"unknown dependency {dependency} referenced by {prompt_id}"

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(prompt_id: str) -> str | None:
        if prompt_id in visiting:
            return f"cycle detected at {prompt_id}"
        if prompt_id in visited:
            return None
        visiting.add(prompt_id)
        for dependency in prompts[prompt_id].get("dependencies", []):
            error = visit(dependency)
            if error:
                return error
        visiting.remove(prompt_id)
        visited.add(prompt_id)
        return None

    for prompt_id in sorted(prompts):
        error = visit(prompt_id)
        if error:
            return error
    return None


def eligible(manifest: dict[str, Any], state: dict[str, Any], prompt_id: str) -> tuple[bool, list[str]]:
    item = get_prompt(manifest, prompt_id)
    reasons: list[str] = []
    graph_error = dependency_graph_error(manifest)
    if graph_error:
        reasons.append(f"manifest dependency graph invalid: {graph_error}")
        return False, reasons
    for dependency in item.get("dependencies", []):
        dep_state = state.get("prompts", {}).get(dependency)
        if dep_state is None:
            reasons.append(f"dependency {dependency} has no state entry")
            continue
        status = dep_state.get("status")
        revision = entry_revision(dep_state)
        approved_revision = effective_approved_revision(dep_state)
        if status not in {"PASS", "DEFERRED"}:
            reasons.append(f"dependency {dependency} status {status} is not PASS/DEFERRED")
        if not dep_state.get("human_approved_at"):
            reasons.append(f"dependency {dependency} has no human approval")
        if approved_revision != revision:
            reasons.append(
                f"dependency {dependency} approval revision {approved_revision!r} "
                f"does not match current revision {revision}"
            )
    current = state.get("prompts", {}).get(prompt_id, {}).get("status")
    if current not in {"NOT_STARTED", "BLOCKED", "IN_PROGRESS"}:
        reasons.append(f"current status {current} cannot be started/resumed")
    return not reasons, reasons


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_snapshot_ignored(path: Path) -> bool:
    return path.name in IGNORED_SNAPSHOT_NAMES or path.suffix == ".pyc"


def validated_write_roots(item: dict[str, Any]) -> list[tuple[str, Path]]:
    """Return normalized safe roots, including missing roots within the repository."""
    root_resolved = ROOT.resolve()
    result: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for raw_root in item.get("write_roots", []):
        if not isinstance(raw_root, str) or not raw_root.strip():
            raise WriteRootError("write_root must be a nonempty relative repository path")
        raw_path = Path(raw_root)
        if raw_path.is_absolute() or ".." in raw_path.parts:
            raise WriteRootError(f"invalid write_root {raw_root!r}: absolute/traversal path")
        if any(segment.rstrip(" .").casefold() == ".git" for segment in raw_path.parts):
            raise WriteRootError(f"invalid write_root {raw_root!r}: .git path segment is forbidden")
        candidate = ROOT / raw_path
        ancestor = candidate
        while not ancestor.exists() and not ancestor.is_symlink():
            if ancestor == ROOT:
                break
            ancestor = ancestor.parent
        if ancestor.is_symlink():
            raise WriteRootError(f"invalid write_root {raw_root!r}: symlink root or ancestor")
        try:
            ancestor_resolved = ancestor.resolve(strict=ancestor.exists())
            candidate_resolved = candidate.resolve(strict=False)
        except OSError as exc:
            raise WriteRootError(f"invalid write_root {raw_root!r}: cannot resolve ({exc})") from exc
        if ((ancestor_resolved != root_resolved and root_resolved not in ancestor_resolved.parents)
                or (candidate_resolved != root_resolved and root_resolved not in candidate_resolved.parents)):
            raise WriteRootError(f"invalid write_root {raw_root!r}: escapes repository")
        if candidate.is_symlink():
            raise WriteRootError(f"invalid write_root {raw_root!r}: symlink root")
        normalized = candidate.relative_to(ROOT).as_posix()
        if normalized not in seen:
            seen.add(normalized)
            result.append((normalized, candidate))
    return result


def snapshot_write_roots(item: dict[str, Any]) -> dict[str, Any]:
    """Hash regular files only; gate state itself is runtime metadata, not an artifact."""
    files: dict[str, str] = {}
    roots: dict[str, str] = {}
    root_resolved = ROOT.resolve()
    state_resolved = STATE_PATH.resolve()
    for normalized, candidate in validated_write_roots(item):
        if not candidate.exists():
            roots[normalized] = "missing"
            continue
        roots[normalized] = "file" if candidate.is_file() else "directory"
        if candidate.is_file():
            paths = [(candidate.parent, [], [candidate.name])]
        else:
            paths = os.walk(candidate, followlinks=False)
        for directory, dirnames, filenames in paths:
            directory_path = Path(directory)
            safe_dirs: list[str] = []
            for name in sorted(dirnames):
                path = directory_path / name
                if name in IGNORED_SNAPSHOT_NAMES:
                    continue
                if path.is_symlink():
                    raise WriteRootError(f"symlink encountered under write_root: {path}")
                safe_dirs.append(name)
            dirnames[:] = safe_dirs
            for filename in sorted(filenames):
                path = directory_path / filename
                if is_snapshot_ignored(path):
                    continue
                if path.is_symlink():
                    raise WriteRootError(f"symlink encountered under write_root: {path}")
                if not path.is_file():
                    continue
                try:
                    resolved_path = path.resolve()
                except OSError as exc:
                    raise WriteRootError(f"cannot resolve snapshot file {path}: {exc}") from exc
                if resolved_path != root_resolved and root_resolved not in resolved_path.parents:
                    raise WriteRootError(f"snapshot file escapes repository: {path}")
                if resolved_path == state_resolved:
                    continue
                files[path.relative_to(ROOT).as_posix()] = sha256_file(path)
    return {"version": 1, "started_at": now(), "roots": dict(sorted(roots.items())),
            "files": dict(sorted(files.items()))}


def snapshot_is_clean(item: dict[str, Any], baseline: dict[str, Any]) -> bool:
    current = snapshot_write_roots(item)
    return current.get("roots") == baseline.get("roots") and current.get("files") == baseline.get("files")


def git_roots_clean(item: dict[str, Any]) -> bool:
    roots = [normalized for normalized, _ in validated_write_roots(item)]
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *roots],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and not result.stdout.strip()


def clean_unsubmitted_entry(entry: dict[str, Any]) -> bool:
    return (
        entry.get("submitted_at") is None
        and entry.get("report") is None
        and not entry.get("evidence", [])
        and not has_current_approval(entry)
    )


def current_approval_snapshot(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "approved_at": entry.get("human_approved_at"),
        "approved_by": entry.get("human_approved_by"),
        "approval_note": entry.get("approval_note"),
        "approved_revision": effective_approved_revision(entry),
        "report": entry.get("report"),
        "evidence": list(entry.get("evidence", [])),
        "submitted_at": entry.get("submitted_at"),
    }


def current_rejection_record(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Find the append-only rejection record for the entry's current revision."""
    revision = entry_revision(entry)
    for record in reversed(rejection_history(entry)):
        if record.get("revision") == revision:
            return copy.deepcopy(record)
    return None


def rejection_snapshot(entry: dict[str, Any], action: str, integrity: str) -> dict[str, Any]:
    return {
        "action": action,
        "revision": entry_revision(entry),
        "rejected_at": entry.get("human_approved_at"),
        "rejected_by": entry.get("human_approved_by"),
        "rejection_note": entry.get("approval_note"),
        "submitted_at": entry.get("submitted_at"),
        "report": entry.get("report"),
        "evidence": list(entry.get("evidence", [])),
        "prior_start_snapshot": copy.deepcopy(entry.get("start_snapshot")),
        "integrity": integrity,
    }


def complete_rejection_disposition(entry: dict[str, Any]) -> bool:
    """Validate the legacy-named fields which record a human rejection."""
    return (
        bool(entry.get("human_approved_at"))
        and isinstance(entry.get("human_approved_by"), str)
        and bool(entry["human_approved_by"].strip())
        and isinstance(entry.get("approval_note"), str)
        and bool(entry["approval_note"].strip())
        and bool(entry.get("submitted_at"))
        and isinstance(entry.get("report"), str)
        and bool(entry["report"].strip())
        and bool(entry.get("evidence"))
        and entry.get("approved_revision") is None
        and effective_approved_revision(entry) is None
    )


def append_approval(entry: dict[str, Any], action: str, stamp: str, by: str, note: str) -> None:
    records = approval_history(entry)
    records.append({
        "action": action,
        "revision": entry_revision(entry),
        "at": stamp,
        "by": by,
        "note": note,
        "report": entry.get("report"),
        "evidence": list(entry.get("evidence", [])),
        "submitted_at": entry.get("submitted_at"),
    })
    entry["approval_history"] = records


def descendants(manifest: dict[str, Any], prompt_id: str) -> list[str]:
    error = dependency_graph_error(manifest)
    if error:
        raise ValueError(f"manifest dependency graph invalid: {error}")
    reverse: dict[str, list[str]] = {key: [] for key in manifest["prompts"]}
    for child, item in manifest["prompts"].items():
        for parent in item.get("dependencies", []):
            reverse[parent].append(child)
    found: set[str] = set()
    pending = sorted(reverse[prompt_id], reverse=True)
    while pending:
        child = pending.pop()
        if child in found:
            continue
        found.add(child)
        pending.extend(sorted(reverse[child], reverse=True))
    return sorted(found)


def command_context(args: argparse.Namespace) -> int:
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    item = get_prompt(manifest, args.prompt_id)
    ok, reasons = eligible(manifest, state, args.prompt_id)
    print(json.dumps({
        "prompt_id": args.prompt_id, "eligible": ok, "reasons": reasons,
        "status": state["prompts"][args.prompt_id]["status"],
        "dependencies": item.get("dependencies", []), "write_roots": item["write_roots"],
        "preferred_agents": item["preferred_agents"], "required_report": item["required_report"],
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
    try:
        validated_write_roots(manifest["prompts"][args.prompt_id])
    except WriteRootError as exc:
        print(f"Cannot start: {exc}", file=sys.stderr)
        return 2
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "IN_PROGRESS":
        try:
            snapshot = snapshot_write_roots(manifest["prompts"][args.prompt_id])
        except WriteRootError as exc:
            print(f"Cannot start: {exc}", file=sys.stderr)
            return 2
        entry.update({
            "status": "IN_PROGRESS", "started_at": now(), "submitted_at": None,
            "start_snapshot": snapshot,
        })
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
    markers = ["Trạng thái", "Đã thay đổi", "Bằng chứng", "Sai lệch", "Đề xuất prompt tiếp theo"]
    absent = [marker for marker in markers if marker not in report_text]
    if absent:
        print("Report missing sections: " + ", ".join(absent), file=sys.stderr)
        return 2
    entry.update({"status": "AWAITING_APPROVAL", "submitted_at": now(),
                  "report": str(report.relative_to(ROOT)),
                  "evidence": [str(path.relative_to(ROOT)) for path in evidence]})
    save_state(state)
    print(f"AWAITING_APPROVAL {args.prompt_id}")
    return 0


def require_human_metadata(args: argparse.Namespace) -> bool:
    if not args.by.strip() or not args.note.strip():
        print("--by and non-empty --note are required", file=sys.stderr)
        return False
    return True


def command_approve(args: argparse.Namespace) -> int:
    if not require_human_metadata(args):
        return 2
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    get_prompt(manifest, args.prompt_id)
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "AWAITING_APPROVAL":
        print(f"Prompt must be AWAITING_APPROVAL, got {entry['status']}", file=sys.stderr)
        return 2
    stamp = now()
    entry.update({"status": "PASS", "human_approved_at": stamp, "human_approved_by": args.by,
                  "approval_note": args.note, "approved_revision": entry_revision(entry)})
    append_approval(entry, "APPROVED", stamp, args.by, args.note)
    save_state(state)
    print(f"PASS {args.prompt_id}")
    return 0


def command_reject(args: argparse.Namespace) -> int:
    if not require_human_metadata(args):
        return 2
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    get_prompt(manifest, args.prompt_id)
    entry = state["prompts"][args.prompt_id]
    if entry["status"] != "AWAITING_APPROVAL":
        print(f"Prompt must be AWAITING_APPROVAL, got {entry['status']}", file=sys.stderr)
        return 2
    stamp = now()
    entry.update({"status": "FAIL", "human_approved_at": stamp, "human_approved_by": args.by,
                  "approval_note": args.note, "approved_revision": None})
    rejections = rejection_history(entry)
    rejections.append(rejection_snapshot(entry, "REJECTED", "PATHS_CAPTURED_AT_REJECTION"))
    entry["rejection_history"] = rejections
    save_state(state)
    print(f"FAIL {args.prompt_id}")
    return 0


def command_defer_group(args: argparse.Namespace) -> int:
    if not require_human_metadata(args):
        return 2
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    targets = sorted(key for key, item in manifest["prompts"].items() if item["group"] == args.group)
    if not targets:
        print(f"Unknown group: {args.group}", file=sys.stderr)
        return 2
    for prompt_id in targets:
        for dependency in manifest["prompts"][prompt_id].get("dependencies", []):
            dep = state["prompts"].get(dependency, {})
            if (dep.get("status") not in {"PASS", "DEFERRED"} or not dep.get("human_approved_at")
                    or effective_approved_revision(dep) != entry_revision(dep)):
                print(f"Cannot defer group {args.group}: dependency {dependency} is not current-revision approved", file=sys.stderr)
                return 2
        if state["prompts"][prompt_id]["status"] != "NOT_STARTED":
            print(f"Cannot defer {prompt_id}: status is {state['prompts'][prompt_id]['status']}", file=sys.stderr)
            return 2
    stamp = now()
    for prompt_id in targets:
        entry = state["prompts"][prompt_id]
        entry.update({"status": "DEFERRED", "human_approved_at": stamp, "human_approved_by": args.by,
                      "approval_note": args.note, "approved_revision": entry_revision(entry)})
        append_approval(entry, "DEFERRED_APPROVED", stamp, args.by, args.note)
    save_state(state)
    print(f"DEFERRED group {args.group}: {len(targets)} prompts")
    return 0


def command_cancel_start(args: argparse.Namespace) -> int:
    if not require_human_metadata(args):
        return 2
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    item = get_prompt(manifest, args.prompt_id)
    entry = state["prompts"][args.prompt_id]
    if entry.get("status") != "IN_PROGRESS":
        print(f"Prompt must be IN_PROGRESS, got {entry.get('status')}", file=sys.stderr)
        return 2
    if not clean_unsubmitted_entry(entry):
        print("Cannot cancel start: submitted/report/evidence/current approval exists", file=sys.stderr)
        return 2
    baseline = entry.get("start_snapshot")
    legacy_snapshot = isinstance(baseline, dict) and "roots" not in baseline
    try:
        validated_write_roots(item)
        clean = git_roots_clean(item) if legacy_snapshot else (
            isinstance(baseline, dict) and snapshot_is_clean(item, baseline)
        ) if baseline is not None else git_roots_clean(item)
    except WriteRootError as exc:
        print(f"Cannot cancel start: {exc}", file=sys.stderr)
        return 2
    if legacy_snapshot:
        if not clean:
            print("Cannot cancel start: artifact baseline unavailable or write_roots are dirty", file=sys.stderr)
            return 2
        snapshot_mode = "legacy_snapshot_git_fallback"
    elif baseline is not None:
        if not clean:
            print("Cannot cancel start: artifacts changed under prompt write_roots", file=sys.stderr)
            return 2
        snapshot_mode = "start_snapshot"
    elif clean:
        snapshot_mode = "git_fallback"
    else:
        print("Cannot cancel start: artifact baseline unavailable or write_roots are dirty", file=sys.stderr)
        return 2
    prior_started_at = entry.get("started_at")
    events = history(entry)
    events.append({"action": "CANCEL_START", "at": now(), "by": args.by, "note": args.note,
                   "revision": entry_revision(entry), "previous_status": "IN_PROGRESS",
                   "previous_started_at": prior_started_at, "snapshot_mode": snapshot_mode})
    entry.update({"status": "NOT_STARTED", "started_at": None, "submitted_at": None, "report": None,
                  "evidence": [], "start_snapshot": None, "last_cancelled_at": events[-1]["at"],
                  "last_cancelled_by": args.by, "last_cancelled_reason": args.note, "history": events})
    save_state(state)
    print(f"NOT_STARTED {args.prompt_id} (cancel-start)")
    return 0


def command_reopen(args: argparse.Namespace) -> int:
    if not require_human_metadata(args):
        return 2
    manifest, state = load(MANIFEST_PATH), load(STATE_PATH)
    item = get_prompt(manifest, args.prompt_id)
    try:
        validated_write_roots(item)
        children = descendants(manifest, args.prompt_id)
    except (WriteRootError, ValueError) as exc:
        print(f"Cannot reopen: {exc}", file=sys.stderr)
        return 2
    entry = state.get("prompts", {}).get(args.prompt_id)
    if not isinstance(entry, dict):
        print(f"Cannot reopen: target {args.prompt_id} has no state entry", file=sys.stderr)
        return 2
    source_status = entry.get("status")
    if source_status not in {"PASS", "FAIL"}:
        print(f"Prompt must be PASS or FAIL, got {source_status}", file=sys.stderr)
        return 2
    if source_status == "PASS":
        if not entry.get("human_approved_at") or effective_approved_revision(entry) != entry_revision(entry):
            print("Cannot reopen: current human approval does not match current revision", file=sys.stderr)
            return 2
    elif not complete_rejection_disposition(entry):
        print("Cannot reopen: FAIL requires a complete current-revision human rejection disposition", file=sys.stderr)
        return 2
    for child_id in children:
        child = state["prompts"].get(child_id)
        if child is None:
            print(f"Cannot reopen: descendant {child_id} has no state entry", file=sys.stderr)
            return 2
        if child.get("status") == "IN_PROGRESS":
            print(f"Cannot reopen: descendant {child_id} is IN_PROGRESS; cancel-start it first", file=sys.stderr)
            return 2
        if (child.get("status") != "NOT_STARTED" or child.get("submitted_at") is not None
                or child.get("report") is not None or child.get("evidence", []) or has_current_approval(child)):
            print(f"Cannot reopen: descendant {child_id} is not pristine NOT_STARTED", file=sys.stderr)
            return 2
    try:
        snapshot = snapshot_write_roots(item)
    except WriteRootError as exc:
        print(f"Cannot reopen: {exc}", file=sys.stderr)
        return 2
    stamp = now()
    old_revision = entry_revision(entry)
    prior_start_snapshot = copy.deepcopy(entry.get("start_snapshot"))
    events = history(entry)
    updates: dict[str, Any] = {}
    event: dict[str, Any] = {
        "action": "REOPENED", "from_revision": old_revision, "to_revision": old_revision + 1,
        "at": stamp, "by": args.by, "note": args.note, "source_status": source_status,
        "prior_start_snapshot": prior_start_snapshot, "descendants_checked": children,
    }
    if source_status == "PASS":
        prior_approval = current_approval_snapshot(entry)
        approvals = approval_history(entry)
        approvals.append({"action": "APPROVAL_ARCHIVED", **prior_approval,
                          "prior_start_snapshot": prior_start_snapshot, "archived_at": stamp,
                          "archived_by": args.by, "archive_reason": args.note})
        updates["approval_history"] = approvals
        event["prior_approval"] = prior_approval
    else:
        prior_rejection = current_rejection_record(entry)
        rejections = rejection_history(entry)
        if prior_rejection is None:
            prior_rejection = rejection_snapshot(entry, "REJECTION_ARCHIVED_LEGACY",
                                                 "NOT_CAPTURED_AT_SUBMIT_LEGACY")
            rejections.append(prior_rejection)
        updates["rejection_history"] = rejections
        event["prior_rejection"] = prior_rejection
    events.append(event)
    entry.update({"status": "IN_PROGRESS", "revision": old_revision + 1, "started_at": stamp,
                   "submitted_at": None, "report": None, "evidence": [], "human_approved_at": None,
                   "human_approved_by": None, "approval_note": None, "approved_revision": None,
                   "reopened_at": stamp, "reopened_by": args.by, "reopen_reason": args.note,
                   "history": events, "start_snapshot": snapshot, **updates})
    save_state(state)
    print(f"IN_PROGRESS {args.prompt_id} revision {old_revision + 1} (reopened from {source_status})")
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
    for name, func in (("approve", command_approve), ("reject", command_reject),
                       ("cancel-start", command_cancel_start), ("reopen", command_reopen)):
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
