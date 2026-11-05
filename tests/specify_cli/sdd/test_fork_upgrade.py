"""Fork release and installer source remain aligned."""

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("repo", ["juftin/spec-kit", "company/mirror"])
def test_release_and_upgrade_use_same_repository(repo):
    env = dict(os.environ, SPECIFY_UPGRADE_REPO=repo)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from specify_cli._version import GITHUB_API_LATEST, _GITHUB_SOURCE_URL; print(GITHUB_API_LATEST); print(_GITHUB_SOURCE_URL)",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"https://api.github.com/repos/{repo}/releases/latest",
        f"git+https://github.com/{repo}.git",
    ]
