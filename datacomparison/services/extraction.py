"""Field extraction strategies."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Protocol


@dataclass
class ExtractionResult:
    field_name: str
    value: Optional[str]
    confidence: float
    raw: Optional[str] = None


class Extractor(Protocol):
    def extract(self, text: str, config: Dict[str, str], field_name: str) -> ExtractionResult:
        ...


class RegexExtractor:
    """Extracts values using regular expressions."""

    def extract(self, text: str, config: Dict[str, str], field_name: str) -> ExtractionResult:
        pattern = config.get("pattern")
        if not pattern:
            raise ValueError("Regex extractor requires a 'pattern'")
        flags = config.get("flags", "")
        re_flags = 0
        if "i" in flags:
            re_flags |= re.IGNORECASE
        compiled = re.compile(pattern, flags=re_flags)
        match = compiled.search(text)
        if not match:
            return ExtractionResult(field_name=field_name, value=None, confidence=0.0, raw=None)

        value = match.groupdict().get("value") if match.groupdict() else match.group(1)
        raw = match.group(0)
        confidence = float(config.get("confidence", 1.0))
        return ExtractionResult(field_name=field_name, value=value, confidence=confidence, raw=raw)


class ExtractorRegistry:
    """Maps strategy names to extractor implementations."""

    def __init__(self) -> None:
        self._registry: Dict[str, Extractor] = {
            "regex": RegexExtractor(),
        }

    def get(self, strategy: str) -> Extractor:
        if strategy not in self._registry:
            raise KeyError(f"No extractor registered for strategy '{strategy}'")
        return self._registry[strategy]


registry = ExtractorRegistry()
