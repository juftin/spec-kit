r"""Windows PowerShell 5.1 execution checks for bare-mode extension helpers.

Reproduce on Windows with .venv\Scripts\python -m pytest -n 0
 tests/extensions/test_bare_powershell51.py. These checks deliberately require
Windows PowerShell, rather than substituting PowerShell Core.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

from tests.extensions.test_update_agent_context_python_parity import make_project
from tests.extensions.test_extension_agent_context import _bundled_script_env

POWERSHELL51 = shutil.which("powershell.exe") if os.name == "nt" else None
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(not POWERSHELL51, reason="Windows PowerShell 5.1 required")
def test_bare_helpers_on_windows_powershell51(tmp_path):
    project = make_project(tmp_path / "project", context_file="CLAUDE.md")
    plan = project / "docs/specs/001-auth/plan.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("# Plan\n", encoding="utf-8")
    env = _bundled_script_env(project)
    context_script = (
        ROOT / "extensions/agent-context/scripts/powershell/update-agent-context.ps1"
    )
    common = ROOT / "extensions/git/scripts/powershell/git-common.ps1"
    command = """
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { exit 99 }
& $env:CONTEXT_SCRIPT
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
. $env:GIT_COMMON
$root = Get-RepoRoot
if ($root -ne $env:SPECIFY_INIT_DIR) { exit 98 }
"""
    env.update(
        CONTEXT_SCRIPT=str(context_script),
        GIT_COMMON=str(common),
        SPECIFY_INIT_DIR=str(project),
    )
    result = subprocess.run(
        [POWERSHELL51, "-NoProfile", "-Command", command],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "docs/specs/001-auth/plan.md" in (project / "CLAUDE.md").read_text(
        encoding="utf-8"
    )
    env["SPECIFY_INIT_DIR"] = str(tmp_path / "missing")
    result = subprocess.run(
        [POWERSHELL51, "-NoProfile", "-Command", ". $env:GIT_COMMON; Get-RepoRoot"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "existing directory" in result.stderr
