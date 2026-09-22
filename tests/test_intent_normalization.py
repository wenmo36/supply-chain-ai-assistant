from ai.intent import normalize_analysis_plan


def _plan(**overrides):
    plan = {
        "intent": "summary",
        "metric": "purchase_amount",
        "dimension": "order_date",
        "limit": None,
        "sort": None,
        "time_granularity": None,
        "period": None,
        "condition": None,
        "date_from": None,
        "date_to": None,
        "filters": [],
    }
    plan.update(overrides)
    return plan


def test_plain_summary_removes_forced_dimension():
    result = normalize_analysis_plan(
        _plan(date_from="2026-08-01", date_to="2026-08-31"),
        "查询2026年8月采购金额",
    )

    assert result["intent"] == "summary"
    assert result["dimension"] is None


def test_calendar_month_without_trend_word_is_summary():
    result = normalize_analysis_plan(
        _plan(
            intent="trend",
            time_granularity="month",
            date_from="2026-08-01",
            date_to="2026-08-31",
        ),
        "查询2026年8月采购金额",
    )

    assert result["intent"] == "summary"
    assert result["dimension"] is None
    assert result["time_granularity"] is None


def test_explicit_monthly_trend_remains_trend():
    result = normalize_analysis_plan(
        _plan(intent="trend", time_granularity="month"),
        "按月查看采购金额趋势",
    )

    assert result["intent"] == "trend"
    assert result["dimension"] == "order_date"
    assert result["time_granularity"] == "month"


def test_unspecified_date_trend_defaults_to_daily_series():
    result = normalize_analysis_plan(
        _plan(intent="trend", time_granularity=None),
        "查看采购金额采购日期趋势",
    )

    assert result["intent"] == "trend"
    assert result["dimension"] == "order_date"
    assert result["time_granularity"] == "day"


def test_each_supplier_becomes_comparison():
    result = normalize_analysis_plan(
        _plan(metric="receipt_rate", dimension="supplier"),
        "各供应商的收货率",
    )

    assert result["intent"] == "comparison"
    assert result["dimension"] == "supplier"


def test_unreceived_ranking_excludes_zero():
    result = normalize_analysis_plan(
        _plan(
            intent="ranking",
            metric="unreceived_qty",
            dimension="material",
        ),
        "未收数量最高的5种物料",
    )

    assert result["condition"] == "unreceived_qty > 0"


def test_over_receipt_question_is_stable_filter():
    result = normalize_analysis_plan(
        _plan(
            intent="ranking",
            metric="over_receipt_qty",
            dimension="order",
            limit=10,
            sort="desc",
        ),
        "哪些采购订单存在超收？",
    )

    assert result["intent"] == "filter"
    assert result["dimension"] == "order"
    assert result["limit"] is None
    assert result["sort"] is None


def test_explicit_multi_metric_comparison_preserves_metric_order():
    result = normalize_analysis_plan(
        _plan(
            intent="comparison",
            metric="purchase_amount",
            dimension="supplier",
            sort="desc",
        ),
        "按供应商比较采购金额、收货率和未收数量",
    )

    assert result["metric"] == "purchase_amount"
    assert result["metrics"] == [
        "purchase_amount",
        "receipt_rate",
        "unreceived_qty",
    ]
