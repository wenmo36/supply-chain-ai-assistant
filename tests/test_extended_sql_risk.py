import pytest

from tools.sql_risk_checker import validate_business_sql


def test_distinct_order_count_is_required():
    plan = {"metric": "purchase_order_count", "intent": "summary"}

    with pytest.raises(ValueError, match="COUNT"):
        validate_business_sql(
            "SELECT COUNT(order_no) FROM purchase_detail",
            plan,
        )

    validate_business_sql(
        "SELECT COUNT(DISTINCT order_no) FROM purchase_detail",
        plan,
    )


def test_monthly_trend_requires_period_expression():
    plan = {
        "metric": "purchase_amount",
        "intent": "trend",
        "time_granularity": "month",
    }

    valid_sql = """
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS period,
        SUM(purchase_qty * unit_price) AS purchase_amount
    FROM purchase_detail
    GROUP BY period
    ORDER BY period
    """

    validate_business_sql(valid_sql, plan)

    with pytest.raises(ValueError, match="month"):
        validate_business_sql(
            """
            SELECT
                order_date,
                SUM(purchase_qty * unit_price) AS purchase_amount
            FROM purchase_detail
            GROUP BY order_date
            ORDER BY order_date
            """,
            plan,
        )


def test_date_range_cannot_be_omitted():
    plan = {
        "metric": "purchase_amount",
        "intent": "summary",
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "filters": [],
    }

    with pytest.raises(ValueError, match="date_from|date_to"):
        validate_business_sql(
            """
            SELECT SUM(purchase_qty * unit_price) AS purchase_amount
            FROM purchase_detail
            """,
            plan,
        )

    validate_business_sql(
        """
        SELECT SUM(purchase_qty * unit_price) AS purchase_amount
        FROM purchase_detail
        WHERE order_date >= '2026-08-01'
          AND order_date <= '2026-08-31'
        """,
        plan,
    )


def test_summary_without_dimension_rejects_grouping():
    plan = {
        "metric": "purchase_amount",
        "intent": "summary",
        "dimension": None,
    }

    with pytest.raises(ValueError, match="GROUP BY"):
        validate_business_sql(
            """
            SELECT order_date,
                   SUM(purchase_qty * unit_price) AS purchase_amount
            FROM purchase_detail
            GROUP BY order_date
            """,
            plan,
        )


def test_unreceived_ranking_rejects_zero_groups():
    plan = {
        "metric": "unreceived_qty",
        "intent": "ranking",
        "dimension": "material",
    }

    with pytest.raises(ValueError, match="排除 0"):
        validate_business_sql(
            """
            SELECT material_code,
                   SUM(GREATEST(purchase_qty - received_qty, 0))
                       AS unreceived_qty
            FROM purchase_detail
            GROUP BY material_code
            ORDER BY unreceived_qty DESC
            LIMIT 5
            """,
            plan,
        )
