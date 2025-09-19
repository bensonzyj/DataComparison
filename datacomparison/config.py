"""Application configuration for the data comparison service."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict


@dataclass
class TemplateConfig:
    """Settings related to template discovery."""

    directory: Path = Path(__file__).resolve().parent / "templates"
    default_template: str = "promise_letter"


@dataclass
class ExtractionConfig:
    """Settings for extraction behaviour."""

    confidence_threshold: float = 0.6
    fuzzy_match_threshold: float = 0.85
    normalizers: Dict[str, str] = field(default_factory=lambda: {
        "date": "datacomparison.utils.normalizers.normalize_date",
        "numeric": "datacomparison.utils.normalizers.normalize_numeric",
    })


@dataclass
class Settings:
    """Global application settings."""

    templates: TemplateConfig = field(default_factory=TemplateConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)

    @property
    def template_directory(self) -> Path:
        return self.templates.directory


settings = Settings()
