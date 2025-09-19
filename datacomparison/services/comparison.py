"""Comparison strategies for extracted data versus system records."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from typing import Any, Dict, Optional, Protocol

from datacomparison.config import settings


@dataclass
class ComparisonOutcome:
    field_name: str
    expected: Optional[str]
    actual: Optional[str]
    passed: bool
    score: float
    message: str = ""


class Comparator(Protocol):
    def compare(
        self,
        field_name: str,
        expected: Optional[str],
        actual: Optional[str],
        config: Dict[str, Any],
    ) -> ComparisonOutcome:
        ...


class ExactComparator:
    def compare(self, field_name: str, expected: Optional[str], actual: Optional[str], config: Dict[str, Any]) -> ComparisonOutcome:
        passed = expected == actual and expected is not None
        score = 1.0 if passed else 0.0
        message = "匹配成功" if passed else "字段值不一致"
        return ComparisonOutcome(field_name, expected, actual, passed, score, message)


class FuzzyComparator:
    def compare(self, field_name: str, expected: Optional[str], actual: Optional[str], config: Dict[str, Any]) -> ComparisonOutcome:
        if expected is None or actual is None:
            return ComparisonOutcome(field_name, expected, actual, False, 0.0, "缺少比较值")
        ratio = SequenceMatcher(None, expected, actual).ratio()
        threshold = float(config.get("threshold", settings.extraction.fuzzy_match_threshold))
        passed = ratio >= threshold
        message = f"相似度 {ratio:.2f}, 阈值 {threshold:.2f}"
        return ComparisonOutcome(field_name, expected, actual, passed, ratio, message)


class NumericComparator:
    def compare(self, field_name: str, expected: Optional[str], actual: Optional[str], config: Dict[str, Any]) -> ComparisonOutcome:
        if expected is None or actual is None:
            return ComparisonOutcome(field_name, expected, actual, False, 0.0, "缺少金额或数值")
        try:
            expected_value = Decimal(expected)
            actual_value = Decimal(actual)
        except (InvalidOperation, ValueError):
            return ComparisonOutcome(field_name, expected, actual, False, 0.0, "无法解析为数值")
        tolerance = Decimal(str(config.get("tolerance", "0")))
        diff = abs(expected_value - actual_value)
        passed = diff <= tolerance
        score = float(max(0, 1 - (diff / (expected_value or Decimal("1"))))) if expected_value else 0.0
        message = f"差值 {diff}, 容差 {tolerance}"
        return ComparisonOutcome(field_name, expected, actual, passed, score, message)


class DateComparator:
    def compare(self, field_name: str, expected: Optional[str], actual: Optional[str], config: Dict[str, Any]) -> ComparisonOutcome:
        passed = expected == actual and expected is not None
        score = 1.0 if passed else 0.0
        message = "日期匹配" if passed else "日期不一致"
        return ComparisonOutcome(field_name, expected, actual, passed, score, message)


class ComparatorRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Comparator] = {
            "exact": ExactComparator(),
            "fuzzy": FuzzyComparator(),
            "numeric": NumericComparator(),
            "date": DateComparator(),
        }

    def get(self, strategy: str) -> Comparator:
        if strategy not in self._registry:
            raise KeyError(f"Unsupported comparison strategy '{strategy}'")
        return self._registry[strategy]


registry = ComparatorRegistry()
