from ai.chart_planner import build_chart_plan


def test_ranking_uses_horizontal_bar_without_model_call():
    plan = {
        "intent": "ranking",
        "metric": "purchase_amount",
        "dimension": "supplier",
        "limit": 5,
        "sort": "desc",
    }

    chart = build_chart_plan(plan)

    assert chart["chart_type"] == "bar_chart"
    assert chart["title"] == "供应商采购金额排名（前5）"
    assert chart["sort"] == "desc"


def test_filter_uses_business_named_table():
    plan = {
        "intent": "filter",
        "metric": "over_receipt_qty",
        "dimension": "order",
        "sort": None,
    }

    chart = build_chart_plan(plan)

    assert chart["chart_type"] == "table"
    assert chart["title"] == "超收数量明细"
