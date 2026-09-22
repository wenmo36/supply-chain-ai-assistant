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


def test_filter_plan_builds_order_detail_table_instead_of_card(tmp_path):
    report_root = tmp_path / "SupplyChainAI.Report"
    pages_root = report_root / "definition" / "pages"
    pages_root.mkdir(parents=True)
    (pages_root / "pages.json").write_text(
        json.dumps({"pageOrder": ["existing-page"], "activePageName": "existing-page"}),
        encoding="utf-8",
    )
    payload = {
        "question": "查询存在超收的采购订单",
        "analysis_plan": {
            "intent": "filter",
            "metric": "over_receipt_qty",
            "dimension": "order",
            "limit": None,
            "sort": None,
        },
        "chart_plan": {
            "chart_type": "table",
            "title": "超收数量明细",
            "x_axis": None,
            "y_axis": None,
        },
        "rows": [
            {"order_no": "CG752610", "over_receipt_qty": 20.0},
            {"order_no": "CG752614", "over_receipt_qty": 50.0},
        ],
    }

    page_path = build_ai_page_from_payload(payload, report_root)
    primary = json.loads(
        (page_path / "visuals" / "f0a1b2c3d4e6" / "visual.json").read_text(
            encoding="utf-8"
        )
    )
    secondary = json.loads(
        (page_path / "visuals" / "f0a1b2c3d4e7" / "visual.json").read_text(
            encoding="utf-8"
        )
    )

    assert primary["visual"]["visualType"] == "pivotTable"
    assert primary["visual"]["query"]["queryState"]["Rows"]["projections"][0]["queryRef"].endswith("order_no")
    assert secondary["isHidden"] is True


def test_multi_metric_comparison_builds_all_value_projections(tmp_path):
    report_root = tmp_path / "SupplyChainAI.Report"
    pages_root = report_root / "definition" / "pages"
    pages_root.mkdir(parents=True)
    (pages_root / "pages.json").write_text(
        json.dumps({"pageOrder": [], "activePageName": ""}),
        encoding="utf-8",
    )
    payload = {
        "question": "按供应商比较采购金额、收货率和未收数量",
        "analysis_plan": {
            "intent": "comparison",
            "metric": "purchase_amount",
            "metrics": [
                "purchase_amount",
                "receipt_rate",
                "unreceived_qty",
            ],
            "dimension": "supplier",
            "sort": "desc",
        },
        "chart_plan": {
            "chart_type": "table",
            "title": "供应商采购金额、收货率、未收数量对比",
            "x_axis": "supplier",
            "y_axis": "purchase_amount",
            "y_axes": [
                "purchase_amount",
                "receipt_rate",
                "unreceived_qty",
            ],
        },
        "rows": [
            {
                "supplier_name": "供应商A",
                "purchase_amount": 100.0,
                "receipt_rate": 80.0,
                "unreceived_qty": 20.0,
            }
        ],
    }

    page_path = build_ai_page_from_payload(payload, report_root)
    primary = json.loads(
        (page_path / "visuals" / "f0a1b2c3d4e6" / "visual.json").read_text(
            encoding="utf-8"
        )
    )
    values = primary["visual"]["query"]["queryState"]["Values"]["projections"]

    assert primary["visual"]["visualType"] == "pivotTable"
    assert [item["queryRef"] for item in values] == [
        "supply_chain_ai purchase_detail.采购金额",
        "supply_chain_ai purchase_detail.收货率",
        "supply_chain_ai purchase_detail.未收数量",
    ]
