import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "orca-wait.sh"
FIXTURE = ROOT / "tests" / "fixtures" / "orca-check-output.txt"


def run_parse(path, path_env="/usr/bin:/bin"):
    env = os.environ.copy()
    env["PATH"] = path_env
    return subprocess.run(
        ["bash", str(SCRIPT), "--parse", str(path)],
        capture_output=True,
        text=True,
        env=env,
    )


def test_parse_ignores_heartbeat_objects_but_preserves_literal(tmp_path):
    result = run_parse(FIXTURE)
    assert result.returncode == 0, result.stderr
    assert "timedOut=false count=1 deliveryId=delivery_123" in result.stdout
    assert "[question] Need decision" in result.stdout
    assert "literal _keepalive string" in result.stdout
    assert 'payload: {"choice":"safe"}' in result.stdout
    assert "quota[claude]: SKIP" in result.stdout


def test_quota_output_is_compact_and_failure_is_fail_open(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    agent_orch = fake_bin / "agent-orch"
    agent_orch.write_text(
        '#!/bin/sh\nprovider="$4"\nprintf \'{"provider":"%s","bucket":"window","used_pct":17,"decision":"allow","cached":true}\\n\' "$provider"\n'
    )
    agent_orch.chmod(0o755)
    result = run_parse(FIXTURE, f"{fake_bin}:/usr/bin:/bin")
    assert result.returncode == 0
    assert "quota[claude]: provider=claude bucket=window used_pct=17 decision=allow" in result.stdout
    assert "cached" not in result.stdout

    agent_orch.write_text("#!/bin/sh\necho 'network unavailable' >&2\nexit 7\n")
    agent_orch.chmod(0o755)
    failed = run_parse(FIXTURE, f"{fake_bin}:/usr/bin:/bin")
    assert failed.returncode == 0
    assert "quota[claude]: SKIP (查詢失敗: network unavailable)" in failed.stdout
    assert "quota[codex]: SKIP (查詢失敗: network unavailable)" in failed.stdout


def test_timeout_exits_three(tmp_path):
    raw = tmp_path / "timeout.log"
    raw.write_text(
        '{"_keepalive":true,"elapsedMs":15000}\n'
        '{"ok":true,"result":{"messages":[],"count":0,"timedOut":true}}\n'
    )
    result = run_parse(raw)
    assert result.returncode == 3
    assert "timedOut=true count=0 deliveryId=-" in result.stdout


def test_error_response_prints_error_code(tmp_path):
    raw = tmp_path / "error.log"
    raw.write_text('{"ok":false,"error":{"code":"consumer_fenced"}}\n')
    result = run_parse(raw)
    assert result.returncode == 1
    assert "ERROR: orca check returned error.code=consumer_fenced" in result.stderr
    assert '"code": "consumer_fenced"' in result.stderr


def test_non_timeout_empty_result_is_error(tmp_path):
    raw = tmp_path / "empty.log"
    raw.write_text('{"ok":true,"result":{"messages":[],"count":0,"timedOut":false}}\n')
    result = run_parse(raw)
    assert result.returncode == 1
    assert "contained no messages" in result.stderr
