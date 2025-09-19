import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from datacomparison.api import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_compare_endpoint_with_text():
    client = TestClient(app)
    payload = {
        "template_id": "promise_letter",
        "system_data": {
            "customer_name": "张三",
            "id_number": "110101199001011234",
            "amount": "100000.00",
            "signing_date": "2024-05-20",
        },
        "document_text": "承诺书\n姓名：张三\n身份证号：110101199001011234\n金额：100,000.00\n日期：2024-05-20",
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pass"
    assert data["fields"]["customer_name"]["passed"] is True
