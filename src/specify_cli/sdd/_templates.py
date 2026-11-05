"""Strict manifest validation at the SDD template boundary."""

from __future__ import annotations

from pathlib import Path

from ..presets import PresetError, PresetManifest, PresetResolver


class SDDTemplateResolver(PresetResolver):
    """Refuse invalid contributing manifests instead of using convention fallbacks."""

    def _get_manifest(self, pack_dir: Path):
        path = pack_dir / "preset.yml"
        if path.exists():
            return PresetManifest(path)
        return None

    def _extension_manifest_declared_template(
        self, ext_dir, template_name, template_type
    ):
        from ..extensions import ExtensionManifest, ValidationError

        path = ext_dir / "extension.yml"
        if path.exists():
            try:
                ExtensionManifest(path)
            except ValidationError as exc:
                raise PresetError(f"Invalid extension manifest {path}: {exc}") from exc
        return super()._extension_manifest_declared_template(
            ext_dir, template_name, template_type
        )
