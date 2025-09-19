"""FastAPI application exposing comparison endpoints."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, root_validator

from datacomparison.services.service import DocumentComparisonService, service
from datacomparison.templates import registry as template_registry


class ComparisonRequest(BaseModel):
    template_id: Optional[str] = Field(None, description="Template identifier")
    system_data: Dict[str, str] = Field(..., description="Canonical business data from core system")
    document_path: Optional[str] = Field(None, description="Path to document to parse")
    document_text: Optional[str] = Field(None, description="Raw text content of document")

    @root_validator
    def validate_source(cls, values):
        if not values.get("document_path") and not values.get("document_text"):
            raise ValueError("document_path 或 document_text 至少提供一个")
        return values


class ComparisonResponse(BaseModel):
    status: str
    template_id: str
    description: str
    fields: Dict[str, Dict[str, object]]


app = FastAPI(title="Data Comparison Service", version="0.1.0")
comparison_service: DocumentComparisonService = service


@app.get("/templates/{template_id}")
async def get_template(template_id: str):
    try:
        template = template_registry.load(template_id)
    except FileNotFoundError as exc:  # pragma: no cover - HTTP path
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "template_id": template.template_id,
        "description": template.description,
        "fields": [
            {
                "name": field.name,
                "extractor": field.extractor,
                "required": field.required,
                "comparison": field.comparison,
                "normalizers": field.normalizer_names,
            }
            for field in template.fields.values()
        ],
    }


@app.post("/compare", response_model=ComparisonResponse)
async def compare(request: ComparisonRequest):
    document_path = Path(request.document_path) if request.document_path else None
    try:
        report = comparison_service.compare(
            template_id=request.template_id,
            system_data=request.system_data,
            document_path=document_path,
            document_text=request.document_text,
        )
    except Exception as exc:  # pragma: no cover - API level error translation
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fields = {
        field.field_name: {
            "extracted_value": field.extracted_value,
            "normalized_value": field.normalized_value,
            "expected_value": field.expected_value,
            "passed": field.passed,
            "score": field.score,
            "message": field.message,
            "confidence": field.confidence,
        }
        for field in report.fields
    }

    return ComparisonResponse(
        status=report.status,
        template_id=report.template_id,
        description=report.description,
        fields=fields,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}
