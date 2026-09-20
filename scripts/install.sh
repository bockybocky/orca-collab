#!/usr/bin/env bash
set -u

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
failures=0

link_skill() {
  local label=$1 destination=$2
  mkdir -p "$(dirname "$destination")"
  if [[ -L "$destination" ]]; then
    local current
    current=$(readlink "$destination")
    if [[ "$current" == "$root" ]]; then
      echo "ok $label: $destination -> $root"
    else
      echo "ERROR $label: $destination already points to $current; not overwriting"
      failures=$((failures + 1))
    fi
  elif [[ -e "$destination" ]]; then
    echo "ERROR $label: $destination already exists and is not a symlink; not overwriting"
    failures=$((failures + 1))
  else
    ln -s "$root" "$destination"
    echo "linked $label: $destination -> $root"
  fi
}

link_skill "Claude Code" "$HOME/.claude/skills/orca-collab"
pi_root=${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}
link_skill "pi" "$pi_root/skills/orca-collab"
link_skill "Codex（~/.agents/skills，pi 也讀）" "$HOME/.agents/skills/orca-collab"

((failures == 0))
