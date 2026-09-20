import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install.sh"


def run_install(tmp_path):
    home = tmp_path / "home"
    pi_root = tmp_path / "pi"
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(pi_root)
    result = subprocess.run(["bash", str(INSTALL)], capture_output=True, text=True, env=env)
    return result, home, pi_root


def test_install_creates_three_links_and_is_idempotent(tmp_path):
    first, home, pi_root = run_install(tmp_path)
    assert first.returncode == 0, first.stdout + first.stderr
    links = (
        home / ".claude" / "skills" / "orca-collab",
        pi_root / "skills" / "orca-collab",
        home / ".agents" / "skills" / "orca-collab",
    )
    assert first.stdout.count("linked ") == 3
    assert all(link.is_symlink() and link.resolve() == ROOT for link in links)

    second, _, _ = run_install(tmp_path)
    assert second.returncode == 0, second.stdout + second.stderr
    assert second.stdout.count("ok ") == 3
    assert all(link.is_symlink() and link.resolve() == ROOT for link in links)


def test_install_refuses_wrong_existing_symlink(tmp_path):
    home = tmp_path / "home"
    wrong = tmp_path / "wrong"
    wrong.mkdir()
    destination = home / ".claude" / "skills" / "orca-collab"
    destination.parent.mkdir(parents=True)
    destination.symlink_to(wrong)

    result, _, _ = run_install(tmp_path)
    assert result.returncode == 1
    assert "ERROR Claude Code" in result.stdout
    assert "not overwriting" in result.stdout
    assert destination.is_symlink() and Path(os.readlink(destination)) == wrong
