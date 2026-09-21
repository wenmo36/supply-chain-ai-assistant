from ai.chart_planner import build_chart_plan
from semantic.glossary import GLOSSARY
from semantic.metrics import METRICS


def test_extended_metrics_have_required_semantics():
    expected = {
        "purchase_order_count",
        "supplier_count",
        "material_count",
        "unreceived_qty",
        "receipt_rate",
        "weighted_unit_price",
    }

    assert expected <= METRICS.keys()
    for metric_name in expected:
        metric = METRICS[metric_name]
        assert metric["fact_table"] == "purchase_detail"
        assert metric["sql_expression"]
        assert metric["unit"]


def test_extended_business_terms_are_mapped():
    assert GLOSSARY["未到货数量"] == "unreceived_qty"
    assert GLOSSARY["到货率"] == "receipt_rate"
    assert GLOSSARY["订单数量"] == "purchase_order_count"


def test_monthly_trend_uses_line_chart():
    chart = build_chart_plan(
        {
            "intent": "trend",
            "metric": "purchase_amount",
            "dimension": "order_date",
            "time_granularity": "month",
            "sort": "asc",
        }
    )

    assert chart["chart_type"] == "line_chart"
    assert chart["x_axis"] == "order_date"
    assert chart["y_axis"] == "purchase_amount"
