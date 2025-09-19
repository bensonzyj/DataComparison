"""High level orchestration service for document comparison."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from datacomparison.config import settings
from datacomparison.services import comparison, extraction
from datacomparison.services.document_parser import ParsedDocument, parse_document
from datacomparison.templates import Template, TemplateRegistry, registry as template_registry


@dataclass
class FieldComparison:
    field_name: str
    extracted_value: Optional[str]
    normalized_value: Optional[str]
    expected_value: Optional[str]
    passed: bool
    score: float
    message: str
    confidence: float
    raw: Optional[str] = None


@dataclass
class ComparisonReport:
    template_id: str
    description: str
    status: str
    fields: List[FieldComparison] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "pass"


class DocumentComparisonService:
    """Service coordinating parsing, extraction and comparison."""

    def __init__(
        self,
        template_registry: TemplateRegistry = template_registry,
        extractor_registry: extraction.ExtractorRegistry = extraction.registry,
        comparator_registry: comparison.ComparatorRegistry = comparison.registry,
    ) -> None:
        self.template_registry = template_registry
        self.extractor_registry = extractor_registry
        self.comparator_registry = comparator_registry

    def _obtain_document_text(self, document_path: Optional[Path], document_text: Optional[str]) -> str:
        if document_text:
            return document_text
        if not document_path:
            raise ValueError("Either document_path or document_text must be provided")
        parsed: ParsedDocument = parse_document(document_path)
        return parsed.get("text", "")

    def _normalize_value(self, value: Optional[str], normalizers: Iterable) -> Optional[str]:
        result = value
        for normalizer in normalizers:
            result = normalizer(result)  # type: ignore[call-arg]
        return result

    def compare(
        self,
        template_id: Optional[str],
        system_data: Dict[str, str],
        document_path: Optional[Path] = None,
        document_text: Optional[str] = None,
    ) -> ComparisonReport:
        template_name = template_id or settings.templates.default_template
        template: Template = self.template_registry.load(template_name)
        text = self._obtain_document_text(document_path, document_text)

        field_results: List[FieldComparison] = []
        overall_passed = True
        for field_template in template.fields.values():
            extractor = self.extractor_registry.get(field_template.extractor.get("strategy", "regex"))
            extracted = extractor.extract(text, field_template.extractor, field_template.name)
            normalized_value = self._normalize_value(extracted.value, field_template.normalizers)
            expected_value = system_data.get(field_template.name)

            comparator = self.comparator_registry.get(field_template.comparison.get("strategy", "exact"))
            comparison_result = comparator.compare(
                field_name=field_template.name,
                expected=expected_value,
                actual=normalized_value or extracted.value,
                config=field_template.comparison,
            )

            passed = comparison_result.passed
            if field_template.required and not passed:
                overall_passed = False
            elif field_template.required and extracted.value is None:
                overall_passed = False

            field_results.append(
                FieldComparison(
                    field_name=field_template.name,
                    extracted_value=extracted.value,
                    normalized_value=normalized_value,
                    expected_value=expected_value,
                    passed=passed,
                    score=comparison_result.score,
                    message=comparison_result.message,
                    confidence=extracted.confidence,
                    raw=extracted.raw,
                )
            )

        status = "pass" if overall_passed else "fail"
        return ComparisonReport(
            template_id=template.template_id,
            description=template.description,
            status=status,
            fields=field_results,
        )


service = DocumentComparisonService()
