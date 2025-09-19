from datacomparison.services.service import DocumentComparisonService


def test_document_comparison_pass():
    service = DocumentComparisonService()
    document_text = """承诺书\n姓名：张三\n身份证号：110101199001011234\n金额：100,000.00\n日期：2024-05-20"""
    system_data = {
        "customer_name": "张三",
        "id_number": "110101199001011234",
        "amount": "100000.00",
        "signing_date": "2024-05-20",
    }

    report = service.compare(template_id="promise_letter", system_data=system_data, document_text=document_text)

    assert report.status == "pass"
    assert all(field.passed for field in report.fields)
    assert report.fields[0].confidence == 1.0


def test_document_comparison_fail_on_mismatch():
    service = DocumentComparisonService()
    document_text = """承诺书\n姓名：李四\n身份证号：110101199001011234\n金额：120,000.00\n日期：2024-05-22"""
    system_data = {
        "customer_name": "张三",
        "id_number": "110101199001011234",
        "amount": "100000.00",
        "signing_date": "2024-05-20",
    }

    report = service.compare(template_id="promise_letter", system_data=system_data, document_text=document_text)

    assert report.status == "fail"
    result_by_field = {field.field_name: field for field in report.fields}
    assert not result_by_field["customer_name"].passed
    assert not result_by_field["amount"].passed
    assert result_by_field["id_number"].passed
