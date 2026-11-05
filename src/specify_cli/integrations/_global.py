"""Home-scoped, bare-rendered integration lifecycle."""

from __future__ import annotations

from pathlib import Path

import typer

from .._console import console
from . import BUILTIN_INTEGRATION_KEYS, get_integration
from ._helpers import _get_speckit_version, _resolve_integration_options
from .manifest import IntegrationManifest


def global_lifecycle(
    action: str,
    key: str | None,
    *,
    force: bool = False,
    script: str | None = None,
    integration_options: str | None = None,
) -> None:
    try:
        if not key or key not in BUILTIN_INTEGRATION_KEYS:
            raise ValueError(
                "--global requires an explicit built-in skills integration (for example claude)"
            )
        integration = get_integration(key)
        root = Path.home()
        raw, parsed = _resolve_integration_options(
            integration, {}, key, integration_options
        )
        if not integration.is_skills_mode(parsed, root):
            raise ValueError(
                "--global supports skills modes only; use claude or a skills-based integration without --commands"
            )
        config = integration.config or {}
        folder = Path(config.get("folder", ""))
        if (
            folder.is_absolute()
            or ".." in folder.parts
            or len(folder.parts) != 1
            or not str(folder).startswith(".")
        ):
            raise ValueError("Integration has no dedicated global skills directory")
        manifest_path = root / ".specify" / "integrations" / f"{key}.manifest.json"
        old = IntegrationManifest.load(key, root) if manifest_path.exists() else None
        if old:
            allowed = folder / "skills"
            for tracked in old.files:
                path = Path(tracked)
                if not path.is_relative_to(allowed) or ".." in path.parts:
                    raise ValueError(
                        f"Global manifest contains a path outside dedicated skills: {tracked}"
                    )
        if action == "uninstall":
            if old is None:
                raise ValueError(f"No global installation found for '{key}'")
            _, preserved = old.uninstall(root, force=force)
            console.print(
                f"Global integration '{key}' uninstalled; {len(preserved)} modified file(s) preserved"
            )
            return
        if old and old.check_modified() and not force:
            raise ValueError(
                "Global integration has modified files; use --force to overwrite"
            )
        if action == "upgrade" and old is None:
            raise ValueError(f"No global installation found for '{key}'")
        if old is None and not force:
            for source in integration.list_command_templates():
                skill = (
                    root
                    / folder
                    / "skills"
                    / f"speckit-{source.stem.replace('.', '-')}"
                    / "SKILL.md"
                )
                if skill.exists() or skill.is_symlink():
                    raise ValueError(
                        f"Global skill already exists without a manifest: {skill}; use --force to overwrite"
                    )
        manifest = IntegrationManifest(key, root, version=_get_speckit_version())
        integration.setup(
            root,
            manifest,
            parsed_options=parsed,
            script_type=script or "sh",
            raw_options=raw,
            events={},
            bare=True,
            force=force,
        )
        manifest.save()
        if old:
            stale = IntegrationManifest(key, root, version="stale-cleanup")
            stale._files = {
                k: v for k, v in old.files.items() if k not in manifest.files
            }
            stale._ownership_modes = {k: old.ownership_modes[k] for k in stale.files}
            stale.uninstall(root, force=force, remove_manifest=False)
        console.print(
            f"Integration '{key}' installed globally in {root}"
            if action == "install"
            else f"Global integration '{key}' {action} complete"
        )
    except (ValueError, OSError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
