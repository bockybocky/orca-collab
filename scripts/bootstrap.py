#!/usr/bin/env python3
"""Create an Orca collaboration briefing skeleton and print operator commands."""

import argparse
import os
import re
import shlex
import sys
from datetime import date
from pathlib import Path

SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
COLLAB_DIR = Path(
    os.environ.get("ORCA_COLLAB_DIR", str(Path.home() / ".claude" / "collab"))
).expanduser()
TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "briefing-template.md"


def fail(message: str) -> "None":
    raise SystemExit(f"ERROR: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="strict lowercase kebab-case slug")
    parser.add_argument("--repo", required=True, help="target repository path")
    parser.add_argument("--mode", required=True, choices=("single", "collab"))
    parser.add_argument("--sessions", type=int, default=None)
    parser.add_argument("--roles", default=None, help="comma-separated role names")
    args = parser.parse_args()

    if not SLUG_RE.fullmatch(args.topic):
        fail("--topic 只准 [a-z0-9-]，且連字號不可在首尾或連續")
    sessions = args.sessions if args.sessions is not None else (1 if args.mode == "single" else 3)
    if sessions < 1:
        fail("--sessions 必須大於 0")
    if args.mode == "single" and sessions != 1:
        fail("single 模式的 --sessions 必須是 1")

    defaults = (
        ["single-worker"]
        if args.mode == "single"
        else ["orchestrator", "implementer", "adversarial-verifier"]
    )
    roles = [r.strip() for r in args.roles.split(",") if r.strip()] if args.roles else defaults
    expected = 1 if args.mode == "single" else sessions
    if len(roles) != expected:
        fail(f"{args.mode} 模式需要 {expected} 個 roles（收到 {len(roles)}）")

    repo = Path(args.repo).expanduser().resolve()
    workdir = COLLAB_DIR / f"{date.today():%Y%m%d}-{args.topic}"
    if workdir.exists():
        fail(f"已存在 {workdir}（請換 topic 或先由 owner 處置）")
    workdir.mkdir(parents=True)

    body = TEMPLATE.read_text(encoding="utf-8")
    mode_note = (
        "single：operator 直接監督一名 worker；沒有第二層席位。"
        if args.mode == "single"
        else "collab：operator 只派 orchestrator；implementer／verifier 由 orchestrator 管理。"
    )
    header = (
        f"<!-- bootstrap mode: {args.mode}; sessions: {sessions}; "
        f"roles: {','.join(roles)}; repo: {repo} -->\n"
        f"> 模式提示：{mode_note}\n\n"
    )
    briefing = workdir / "briefing.md"
    briefing.write_text(header + body, encoding="utf-8")

    qrepo = shlex.quote(str(repo))
    role = "single-worker" if args.mode == "single" else "orchestrator"
    objective = f"<待填：{args.topic} 的完整目標>"
    spec = (
        f"Target: {repo}. Change: <待填>. Constraints: <待填>. "
        f"Ownership: <待填>. Observable acceptance: <待填>. Role: {role}."
    )
    print(f"workdir : {workdir}")
    print(f"briefing: {briefing}")
    print(f"mode    : {args.mode} ({mode_note})")
    print("\noperator 指令序列（填完 briefing 後逐步執行）：")
    print(f"1. orca repo add --path {qrepo} --json  # 未登錄才跑")
    print("2. C=$(orca terminal create --worktree current --command zsh --json | jq -r .result.terminal.handle)")
    print(f"3. R=$(orca orchestration run-create --objective {shlex.quote(objective)} --from \"$C\" --json | jq -r .result.run.id)")
    print(
        "4. orca orchestration worker-start "
        f"--spec {shlex.quote(spec)} --worktree new-child --name {shlex.quote(args.topic)} "
        "--run \"$R\" --from \"$C\" --agent claude --json  # agent 可換"
    )
    print(
        "5. orca orchestration check --run \"$R\" --terminal \"$C\" --wait "
        "--types \"worker_done,escalation,question\" --timeout-ms 300000 --json"
    )
    if args.mode == "collab":
        print("6. orchestrator 依 briefing 開 implementer／verifier；巢狀關閉時走 B 路線。")
    else:
        print("6. operator 直接等 single worker 的 question／escalation／worker_done。")


if __name__ == "__main__":
    main()
