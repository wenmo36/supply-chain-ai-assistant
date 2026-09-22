import json

from integrations.powerbi_report_builder import (
    AI_PAGE_ID,
    build_ai_page_from_payload,
)


def test_build_ai_page_creates_bound_visuals_and_dimension_filter(tmp_path):
    report_root = tmp_path / "SupplyChainAI.Report"
    pages_root = report_root / "definition" / "pages"
    pages_root.mkdir(parents=True)
    (pages_root / "pages.json").write_text(
        json.dumps(
            {
                "$schema": "pagesMetadata",
                "pageOrder": ["existing-page"],
                "activePageName": "existing-page",
            }
        ),
        encoding="utf-8",
    )
    payload = {
        "question": "查询采购金额最高的5个供应商",
        "analysis_plan": {
            "intent": "ranking",
            "metric": "purchase_amount",
            "dimension": "supplier",
            "limit": 5,
            "sort": "desc",
        },
        "chart_plan": {
            "chart_type": "bar_chart",
            "title": "供应商采购金额排名（前5）",
            "x_axis": "supplier",
            "y_axis": "purchase_amount",
        },
        "rows": [
            {"supplier_name": "供应商A", "purchase_amount": 100.0},
            {"supplier_name": "供应商B", "purchase_amount": 80.0},
        ],
    }

    page_path = build_ai_page_from_payload(payload, report_root)

    pages = json.loads((pages_root / "pages.json").read_text(encoding="utf-8"))
    chart = json.loads(
        (page_path / "visuals" / "f0a1b2c3d4e6" / "visual.json").read_text(
            encoding="utf-8"
        )
    )
    table = json.loads(
        (page_path / "visuals" / "f0a1b2c3d4e7" / "visual.json").read_text(
            encoding="utf-8"
        )
    )

    assert page_path.name == AI_PAGE_ID
    assert pages["pageOrder"] == ["existing-page", AI_PAGE_ID]
    assert pages["activePageName"] == AI_PAGE_ID
    assert chart["visual"]["visualType"] == "barChart"
    assert chart["visual"]["query"]["queryState"]["Y"]["projections"][0]["queryRef"].endswith("采购金额")
    assert chart["filterConfig"]["filters"][0]["type"] == "Categorical"
    assert chart["filterConfig"]["filters"][0]["field"]["Column"]["Property"] == "supplier_name"
    assert chart["visual"]["query"]["sortDefinition"]["sort"][0]["direction"] == "Descending"
    assert table["visual"]["visualType"] == "pivotTable"
