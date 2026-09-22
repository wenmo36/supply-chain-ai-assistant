import json
from datetime import date
from decimal import Decimal

from ai.analysis_result import AnalysisResult
from integrations.powerbi_adapter import (
    POWERBI_SCHEMA_VERSION,
    build_powerbi_payload,
    write_powerbi_payload,
)


def make_result() -> AnalysisResult:
    return AnalysisResult(
        question="查询采购金额最高的供应商",
        analysis_plan={"metric": "purchase_amount", "group_by": ["supplier_name"]},
        sql="SELECT supplier_name, SUM(purchase_qty * unit_price) AS amount FROM purchase_detail",
        rows=[{"supplier_name": "供应商A", "amount": Decimal("12.50"), "as_of": date(2026, 8, 1)}],
        chart_plan={"chart_type": "bar", "x": "supplier_name", "y": "amount"},
        repair_count=1,
    )


def test_build_powerbi_payload_is_versioned_and_json_safe():
    payload = build_powerbi_payload(make_result())

    assert payload["schema_version"] == POWERBI_SCHEMA_VERSION
    assert payload["question"] == "查询采购金额最高的供应商"
    assert payload["rows"] == [
        {"supplier_name": "供应商A", "amount": 12.5, "as_of": "2026-08-01"}
    ]
    assert "AI_API_KEY" not in json.dumps(payload, ensure_ascii=False)
    json.dumps(payload, ensure_ascii=False)


def test_write_powerbi_payload_replaces_target_atomically(tmp_path):
    target = tmp_path / "nested" / "latest_analysis.json"

    returned = write_powerbi_payload(make_result(), target)

    assert returned == target
    assert target.exists()
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["schema_version"] == POWERBI_SCHEMA_VERSION
    assert saved["repair_count"] == 1
    assert not list(target.parent.glob(".*.tmp"))
