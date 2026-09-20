import os
import plistlib
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "launchd" / "install-launchd.sh"
WRAPPER = ROOT / "launchd" / "orca-serve.sh"


def test_install_launchd_writes_linted_plist_with_required_keys(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    out = tmp_path / "agents"
    env = os.environ.copy()
    env["HOME"] = str(home)
    result = subprocess.run(
        ["bash", str(INSTALL), "--ip", "100.64.0.7", "--out", str(out)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    plist_path = out / "com.user.orca-serve.plist"
    if shutil.which("plutil"):  # macOS 才有；Linux CI 靠下面的 plistlib.load 驗
        lint = subprocess.run(["plutil", "-lint", str(plist_path)], capture_output=True, text=True)
        assert lint.returncode == 0, lint.stderr
    with plist_path.open("rb") as handle:
        data = plistlib.load(handle)
    for key in ("ProgramArguments", "EnvironmentVariables", "RunAtLoad", "KeepAlive"):
        assert key in data
    assert data["ProgramArguments"][0] == "/bin/bash"
    wrapper_path = Path(data["ProgramArguments"][1])
    assert wrapper_path == WRAPPER and wrapper_path.is_file()
    assert data["EnvironmentVariables"]["ORCA_TELEMETRY_DISABLED"] == "1"
    assert data["EnvironmentVariables"]["ORCA_SERVE_ARGS"] == "--pairing-address 100.64.0.7"
    assert data["RunAtLoad"] is True
    assert data["KeepAlive"] is True
    assert str(home) in data["StandardOutPath"]
    assert "not executed: launchctl bootstrap" in result.stdout


def test_missing_ip_fails_without_writing(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    # Keep only required system commands; there is deliberately no tailscale.
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:/usr/bin:/bin"
    out = tmp_path / "agents"
    result = subprocess.run(
        ["bash", str(INSTALL), "--out", str(out)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "pass --ip" in result.stderr
    assert not (out / "com.user.orca-serve.plist").exists()


def _fake_orca(path):
    path.write_text("#!/bin/sh\nexit 3\n")
    path.chmod(0o755)


def test_wrapper_loops_without_storm(tmp_path):
    fake_orca = tmp_path / "orca"
    _fake_orca(fake_orca)
    env = os.environ.copy()
    env.update(
        ORCA_BIN=str(fake_orca),
        ORCA_WRAPPER_RETRY_SLEEP="0.2",
        ORCA_WRAPPER_DESKTOP_PATTERN=f"never-match-{uuid.uuid4()}",
    )
    process = subprocess.Popen(
        ["/bin/bash", str(WRAPPER)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    time.sleep(1.5)
    process.terminate()
    output, _ = process.communicate(timeout=3)
    exit_count = output.count("orca serve exited rc=3")
    assert 2 <= exit_count <= 12
    assert process.returncode != -9


def test_wrapper_starts_with_unset_serve_args_on_bash_32(tmp_path):
    fake_orca = tmp_path / "orca"
    fake_orca.write_text('#!/bin/sh\nprintf "fake orca args: %s\\n" "$*"\nexit 3\n')
    fake_orca.chmod(0o755)
    env = os.environ.copy()
    env.pop("ORCA_SERVE_ARGS", None)
    env.update(
        ORCA_BIN=str(fake_orca),
        ORCA_WRAPPER_RETRY_SLEEP="0.2",
        ORCA_WRAPPER_DESKTOP_PATTERN=f"never-match-{uuid.uuid4()}",
    )
    process = subprocess.Popen(
        ["/bin/bash", str(WRAPPER)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    time.sleep(0.5)
    process.terminate()
    output, _ = process.communicate(timeout=3)
    assert "fake orca args: serve" in output
    assert "unbound variable" not in output
    assert process.returncode != -9


def test_wrapper_waits_for_desktop(tmp_path):
    fake_orca = tmp_path / "orca"
    _fake_orca(fake_orca)
    marker = f"orca-desktop-test-{uuid.uuid4()}"
    desktop = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)", marker])
    env = os.environ.copy()
    env.update(
        ORCA_BIN=str(fake_orca),
        ORCA_WRAPPER_DESKTOP_PATTERN=marker,
        ORCA_WRAPPER_DESKTOP_SLEEP="0.2",
    )
    process = subprocess.Popen(
        ["/bin/bash", str(WRAPPER)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    try:
        time.sleep(1)
        process.terminate()
        output, _ = process.communicate(timeout=3)
    finally:
        desktop.terminate()
        desktop.wait(timeout=3)
    assert output.count("desktop running, sleep 0.2") == 1
    assert "starting orca serve" not in output
    assert process.returncode != -9
