#!/usr/bin/env bash
set -u

orca_bin=${ORCA_BIN:-/opt/homebrew/bin/orca}
serve_args_text=${ORCA_SERVE_ARGS:-}
desktop_pattern=${ORCA_WRAPPER_DESKTOP_PATTERN:-Orca.app/Contents/MacOS/Orca$}
desktop_sleep=${ORCA_WRAPPER_DESKTOP_SLEEP:-30}
retry_sleep=${ORCA_WRAPPER_RETRY_SLEEP:-5}
child_pid=""
desktop_reported=0

stop_wrapper() {
  trap - TERM INT
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  exit 0
}
trap stop_wrapper TERM INT

while true; do
  if pgrep -f -- "$desktop_pattern" >/dev/null 2>&1; then
    if ((desktop_reported == 0)); then
      echo "desktop running, sleep $desktop_sleep"
      desktop_reported=1
    fi
    sleep "$desktop_sleep" &
    child_pid=$!
    wait "$child_pid" 2>/dev/null || true
    child_pid=""
    continue
  fi

  desktop_reported=0
  echo "starting orca serve"
  serve_args=()
  if [[ -n "$serve_args_text" ]]; then
    read -r -a serve_args <<<"$serve_args_text"
  fi
  "$orca_bin" serve ${serve_args[@]+"${serve_args[@]}"} &
  child_pid=$!
  wait "$child_pid"
  rc=$?
  child_pid=""
  echo "orca serve exited rc=$rc"
  sleep "$retry_sleep" &
  child_pid=$!
  wait "$child_pid" 2>/dev/null || true
  child_pid=""
done
