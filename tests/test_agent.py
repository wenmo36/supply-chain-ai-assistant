"""
V2 Analysis Agent 测试

测试：
1. 供应商采购金额 TOP5
2. 采购订单超收
"""

import pytest

from ai.agent import run_analysis


pytestmark = pytest.mark.e2e


def test_supplier_purchase_top5():
    """
    测试供应商采购金额 TOP5。
    """

    result = run_analysis(
        "查询采购金额最高的5个供应商"
    )

    assert (
        result.analysis_plan["metric"]
        == "purchase_amount"
    )

    assert (
        result.analysis_plan["dimension"]
        == "supplier"
    )

    assert "purchase_detail" in result.sql
    assert "purchase_qty" in result.sql
    assert "unit_price" in result.sql

    assert len(result.rows) <= 5

    assert result.repair_count <= 2

    assert result.chart_plan["chart_type"] == "bar_chart"


def test_over_receipt_orders():
    """
    测试采购订单超收分析。
    """

    result = run_analysis(
        "哪些采购订单存在超收？"
    )

    assert (
        result.analysis_plan["metric"]
        == "over_receipt_qty"
    )

    assert (
        result.analysis_plan["dimension"]
        == "order"
    )

    assert "purchase_detail" in result.sql
    assert "SUM(received_qty)" in result.sql
    assert "SUM(purchase_qty)" in result.sql
    assert "GROUP BY order_no" in result.sql

    assert result.repair_count <= 2

    assert result.chart_plan["chart_type"] == "table"


def test_month_range_purchase_amount_is_summary():
    result = run_analysis("查询2026年8月采购金额")

    assert result.analysis_plan["intent"] == "summary"
    assert result.analysis_plan["dimension"] is None
    assert result.analysis_plan["date_from"] == "2026-08-01"
    assert result.analysis_plan["date_to"] == "2026-08-31"
    assert "GROUP BY" not in result.sql.upper()
    assert len(result.rows) == 1
    assert float(result.rows[0]["purchase_amount"]) == 67300
    assert result.chart_plan["chart_type"] == "card"


def test_unreceived_material_ranking_excludes_zero():
    result = run_analysis("未收数量最高的5种物料")

    assert result.analysis_plan["metric"] == "unreceived_qty"
    assert result.analysis_plan["condition"] == "unreceived_qty > 0"
    assert result.rows
    assert all(float(row["unreceived_qty"]) > 0 for row in result.rows)


def test_supplier_receipt_rate_is_comparison():
    result = run_analysis("各供应商的收货率")

    assert result.analysis_plan["intent"] == "comparison"
    assert result.analysis_plan["dimension"] == "supplier"
    assert result.analysis_plan["metric"] == "receipt_rate"
    assert "GROUP BY" in result.sql.upper()
    assert result.chart_plan["chart_type"] == "column_chart"
