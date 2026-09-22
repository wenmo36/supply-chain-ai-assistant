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


def test_over_receipt_supplier_comparison_does_not_require_order_grouping():
    plan = {
        "intent": "comparison",
        "metric": "purchase_amount",
        "metrics": ["purchase_amount", "receipt_rate", "over_receipt_qty"],
        "dimension": "supplier",
        "sort": "desc",
    }

    validate_business_sql(
        """
        SELECT supplier_id,
               SUM(purchase_qty * unit_price) AS purchase_amount,
               SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) * 100
                   AS receipt_rate,
               SUM(GREATEST(received_qty - purchase_qty, 0))
                   AS over_receipt_qty
        FROM purchase_detail
        GROUP BY supplier_id
        """,
        plan,
    )


def test_supplier_over_receipt_aggregate_cannot_be_summed_after_detail_join():
    plan = {
        "intent": "comparison",
        "metric": "purchase_amount",
        "metrics": ["purchase_amount", "receipt_rate", "over_receipt_qty"],
        "dimension": "supplier",
    }

    with pytest.raises(ValueError, match="回连采购明细|重复"):
        validate_business_sql(
            """
            SELECT pd.supplier_id,
                   SUM(pd.purchase_qty * pd.unit_price) AS purchase_amount,
                   SUM(pd.received_qty) /
                       NULLIF(SUM(pd.purchase_qty), 0) * 100 AS receipt_rate,
                   SUM(COALESCE(over_receipt.over_receipt_qty, 0))
                       AS over_receipt_qty
            FROM purchase_detail pd
            LEFT JOIN (
                SELECT supplier_id,
                       SUM(received_qty) - SUM(purchase_qty)
                           AS over_receipt_qty
                FROM purchase_detail
                GROUP BY supplier_id
            ) over_receipt
              ON over_receipt.supplier_id = pd.supplier_id
            GROUP BY pd.supplier_id
            """,
            plan,
        )
