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
