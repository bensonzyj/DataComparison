"""Template loading utilities for document field extraction."""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

try:  # optional dependency when using YAML templates
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from datacomparison.config import settings


@dataclass
class FieldTemplate:
    """Definition of a field to extract from documents."""

    name: str
    extractor: Dict[str, Any]
    required: bool = True
    comparison: Dict[str, Any] = None
    normalizers: List[Callable[[Optional[str]], Optional[str]]] = field(default_factory=list)
    normalizer_names: List[str] = field(default_factory=list)


@dataclass
class Template:
    """Encapsulates template metadata and field definitions."""

    template_id: str
    description: str
    fields: Dict[str, FieldTemplate]


class TemplateRegistry:
    """Loads template definitions from YAML files."""

    def __init__(self, base_path: Optional[Path] = None) -> None:
        self._base_path = base_path or settings.template_directory
        self._cache: Dict[str, Template] = {}

    def _load_yaml(self, template_file: Path) -> Dict[str, Any]:
        if yaml is None:
            raise RuntimeError("Loading YAML templates requires the optional dependency PyYAML")
        with template_file.open("r", encoding="utf-8") as stream:
            return yaml.safe_load(stream)

    def _resolve_normalizers(self, normalizer_names: Iterable[str]):
        resolved = []
        for name in normalizer_names:
            target = settings.extraction.normalizers.get(name)
            if not target:
                raise KeyError(f"Unknown normalizer '{name}' defined in template")
            module_name, func_name = target.rsplit(".", 1)
            module = importlib.import_module(module_name)
            resolved.append(getattr(module, func_name))
        return resolved

    def load(self, template_id: str) -> Template:
        if template_id in self._cache:
            return self._cache[template_id]

        template_file = None
        for extension in (".yaml", ".yml", ".json"):
            candidate = self._base_path / f"{template_id}{extension}"
            if candidate.exists():
                template_file = candidate
                break
        if template_file is None:
            raise FileNotFoundError(f"Template '{template_id}' not found in {self._base_path}")

        if template_file.suffix in {".yaml", ".yml"}:
            data = self._load_yaml(template_file)
        else:
            with template_file.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        tpl_data = data.get("template", {})
        description = tpl_data.get("description", "")
        fields: Dict[str, FieldTemplate] = {}
        for field in tpl_data.get("fields", []):
            normalizer_names = list(field.get("normalizers", []))
            normalizers = self._resolve_normalizers(normalizer_names)
            fields[field["name"]] = FieldTemplate(
                name=field["name"],
                extractor=field["extractor"],
                required=field.get("required", True),
                comparison=field.get("comparison", {"strategy": "exact"}),
                normalizers=list(normalizers),
                normalizer_names=normalizer_names,
            )

        template = Template(template_id=template_id, description=description, fields=fields)
        self._cache[template_id] = template
        return template


registry = TemplateRegistry()
