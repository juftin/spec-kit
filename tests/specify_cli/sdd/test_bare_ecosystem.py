"""Bare template registration and bundled workflow contracts."""

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.agents import CommandRegistrar
from specify_cli.integrations.base import IntegrationBase
from specify_cli.workflows._operation_list import WorkflowListRequest, list_workflows
from specify_cli.workflows.engine import WorkflowEngine
from specify_cli.workflows.overlay.resolver import WorkflowResolver


@pytest.fixture
def bare(tmp_path):
    (tmp_path / ".specify").mkdir()
    (tmp_path / ".specify/init-options.json").write_text(
        json.dumps({"footprint": "bare"})
    )
    return tmp_path


@pytest.mark.parametrize(
    "scripts, expected",
    [
        (
            {
                "ps": "scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -IncludeTasks -Template plan"
            },
            "specify feature check --json --require-spec --include-tasks --template plan",
        ),
        (
            {"ps": "scripts/powershell/setup-plan.ps1 -Json"},
            "specify plan setup --json",
        ),
        ({"py": "scripts/python/setup_tasks.py --json"}, "specify tasks setup --json"),
        (
            {"sh": "scripts/bash/resolve-template.sh spec-template --json"},
            "specify template spec-template --json",
        ),
        ({"cli": "specify custom"}, "specify custom"),
        ({"sh": "custom.sh"}, None),
    ],
)
def test_script_translation(scripts, expected):
    assert IntegrationBase.resolve_bare_script_command(scripts) == expected


def test_registrar_translates_powershell_only_templates(bare):
    body = CommandRegistrar.resolve_skill_placeholders(
        "claude",
        {
            "scripts": {
                "ps": "scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks"
            }
        },
        "Run {SCRIPT}",
        bare,
    )
    assert body == "Run specify feature check --json --require-tasks"


def test_bundled_workflow_is_read_only_default(bare, monkeypatch):
    monkeypatch.chdir(bare)
    engine = WorkflowEngine(bare)
    assert engine.load_workflow("speckit").id == "speckit"
    assert WorkflowResolver(bare).resolve_with_layers("speckit")[0].id == "speckit"
    assert any(
        item.id == "speckit" for item in list_workflows(WorkflowListRequest(bare)).items
    )
    for args in (
        ["workflow", "list"],
        ["workflow", "info", "speckit"],
        ["workflow", "resolve", "speckit"],
    ):
        result = CliRunner().invoke(app, args)
        assert result.exit_code == 0, result.output
    assert not (bare / ".specify/workflows").exists()
    with pytest.raises(FileNotFoundError):
        engine.load_workflow("unknown")


def test_registered_disabled_workflow_does_not_use_bundled_default(bare, monkeypatch):
    from specify_cli.workflows._bundled import bundled_workflow
    from specify_cli.workflows.catalog import WorkflowRegistry

    monkeypatch.setattr(WorkflowRegistry, "get", lambda *args: {"enabled": False})
    assert bundled_workflow(bare, "speckit") is None


def test_scaffold_does_not_inherit_bare_workflows(bare):
    (bare / ".specify/init-options.json").write_text('{"footprint":"scaffold"}')
    with pytest.raises(FileNotFoundError):
        WorkflowEngine(bare).load_workflow("speckit")
