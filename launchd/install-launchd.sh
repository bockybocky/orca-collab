#!/usr/bin/env bash
set -u

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
template="$script_dir/com.user.orca-serve.plist"
out_dir="$HOME/Library/LaunchAgents"
ip=""

while (($#)); do
  case "$1" in
    --out) [[ $# -ge 2 ]] || { echo "FAIL --out needs a directory" >&2; exit 1; }; out_dir=$2; shift 2 ;;
    --ip) [[ $# -ge 2 ]] || { echo "FAIL --ip needs an address" >&2; exit 1; }; ip=$2; shift 2 ;;
    -h|--help) echo "usage: $0 [--ip <TAILSCALE_IP>] [--out <directory>]"; exit 0 ;;
    *) echo "FAIL unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$ip" ]]; then
  if command -v tailscale >/dev/null 2>&1; then
    ip=$(tailscale ip -4 2>/dev/null | head -n 1)
  fi
  if [[ -z "$ip" ]]; then
    echo "FAIL cannot detect Tailscale IPv4; pass --ip <address>" >&2
    exit 1
  fi
fi
if [[ ! "$ip" =~ ^[0-9a-fA-F:.]+$ ]]; then
  echo "FAIL invalid IP address: $ip" >&2
  exit 1
fi

mkdir -p "$out_dir"
destination="$out_dir/com.user.orca-serve.plist"
wrapper="$script_dir/orca-serve.sh"
python3 - "$template" "$destination" "$ip" "$HOME" "$wrapper" <<'PY'
import sys
from pathlib import Path
source, destination, ip, home, wrapper = sys.argv[1:]
text = Path(source).read_text(encoding="utf-8")
text = text.replace("&lt;TAILSCALE_IP&gt;", ip)
text = text.replace("&lt;HOME&gt;", home)
text = text.replace("&lt;WRAPPER_PATH&gt;", wrapper)
Path(destination).write_text(text, encoding="utf-8")
PY

# plutil 只有 macOS 有；沒有就用 plistlib 驗（CI 的 Linux 也能跑）
if command -v plutil >/dev/null 2>&1; then
  lint_ok=0; plutil -lint "$destination" || lint_ok=1
else
  lint_ok=0; python3 -c 'import plistlib,sys; plistlib.load(open(sys.argv[1],"rb"))' "$destination" || lint_ok=1
fi
if ((lint_ok != 0)); then
  echo "FAIL plist lint: $destination" >&2
  exit 1
fi

echo "PASS wrote $destination"
echo "not executed: launchctl bootstrap gui/$(id -u) $destination"
echo "not executed: launchctl bootout gui/$(id -u)/com.user.orca-serve"
