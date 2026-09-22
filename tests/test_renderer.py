"""
Visualization Renderer 测试

测试：
1. 中文字体
2. Dimension 字段映射
3. Metric 字段映射
4. Bar Chart 渲染
5. Table 渲染
"""

from ai.analysis_result import AnalysisResult
from matplotlib.axes import Axes
from unittest.mock import patch

from visualization.renderer import (
    _display_name,
    _format_value,
    _resolve_column,
    _sort_table_rows,
    get_font_status,
    render
)


def test_business_labels_and_number_formatting():
    assert _display_name("supplier") == "供应商"
    assert _display_name("order_no") == "采购订单号"
    assert _display_name("purchase_amount") == "采购金额"
    assert _format_value(23300.0, "purchase_amount") == "¥23,300"
    assert _format_value(20.0, "over_receipt_qty") == "20"
    assert _format_value(87.5, "receipt_rate") == "87.50%"


def test_time_dimension_maps_to_period_alias():
    rows = [{"period": "2026-08", "purchase_amount": 1000}]
    assert _resolve_column(rows, "order_date") == "period"


def test_chinese_font_configured():
    """
    验证中文字体已经配置。
    """

    status = get_font_status()

    assert status
    assert (
        "中文字体：" in status
        or "未找到可用中文字体" in status
    )


def test_dimension_field_mapping():
    """
    验证：
    supplier → supplier_name
    """

    rows = [
        {
            "supplier_name": "测试供应商",
            "purchase_amount": 1000
        }
    ]

    column = _resolve_column(
        rows,
        "supplier"
    )

    assert column == "supplier_name"


def test_metric_field_mapping():
    """
    验证：
    purchase_amount → purchase_amount
    """

    rows = [
        {
            "supplier_name": "测试供应商",
            "purchase_amount": 1000
        }
    ]

    column = _resolve_column(
        rows,
        "purchase_amount"
    )

    assert column == "purchase_amount"


def test_bar_chart_render():
    """
    验证 Bar Chart 可以正常生成 PNG。
    """

    result = AnalysisResult(
        question="测试",
        analysis_plan={
            "intent": "ranking",
            "metric": "purchase_amount",
            "dimension": "supplier"
        },
        sql="SELECT ...",
        rows=[
            {
                "supplier_name": "供应商A",
                "purchase_amount": 1000
            },
            {
                "supplier_name": "供应商B",
                "purchase_amount": 800
            }
        ],
        chart_plan={
            "chart_type": "bar_chart",
            "title": "测试采购金额",
            "x_axis": "supplier",
            "y_axis": "purchase_amount",
            "sort": "desc",
            "orientation": "horizontal",
            "show_data_labels": True
        }
    )

    path = render(result)

    assert path.exists()
    assert path.suffix.lower() == ".png"


def test_table_render():
    """
    验证 Table 可以正常生成 PNG。
    """

    result = AnalysisResult(
        question="测试",
        analysis_plan={
            "intent": "filter",
            "metric": "over_receipt_qty",
            "dimension": "order"
        },
        sql="SELECT ...",
        rows=[
            {
                "order_no": "CG752610",
                "over_receipt_qty": 20
            }
        ],
        chart_plan={
            "chart_type": "table",
            "title": "测试超收表格",
            "x_axis": None,
            "y_axis": None,
            "sort": None,
            "orientation": None,
            "show_data_labels": False
        }
    )

    path = render(result)

    assert path.exists()
    assert path.suffix.lower() == ".png"


def test_single_point_line_chart_does_not_fallback_to_bar(tmp_path):
    """A one-period trend remains a line chart in the local PNG."""

    result = AnalysisResult(
        question="按月查看采购金额趋势",
        analysis_plan={
            "intent": "trend",
            "metric": "purchase_amount",
            "dimension": "order_date",
            "time_granularity": "month",
        },
        sql="SELECT '2026-08' AS period, 67300 AS purchase_amount",
        rows=[{"period": "2026-08", "purchase_amount": 67300.0}],
        chart_plan={
            "chart_type": "line_chart",
            "title": "采购金额采购日期趋势",
            "x_axis": "order_date",
            "y_axis": "purchase_amount",
            "sort": "asc",
            "orientation": None,
            "show_data_labels": False,
        },
    )

    with patch.object(
        Axes,
        "bar",
        side_effect=AssertionError("line_chart 不应退化成 bar_chart"),
    ):
        from visualization.renderer import _render_line_chart

        output_path = _render_line_chart(result, tmp_path / "trend.png")

    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_filter_detail_table_sorts_by_exception_quantity_descending():
    result = AnalysisResult(
        question="查询存在超收的采购订单",
        analysis_plan={
            "intent": "filter",
            "metric": "over_receipt_qty",
            "dimension": "order",
            "sort": None,
        },
        sql="SELECT order_no, over_receipt_qty FROM purchase_detail",
        rows=[
            {"order_no": "CG752610", "over_receipt_qty": 20.0},
            {"order_no": "CG752614", "over_receipt_qty": 50.0},
        ],
        chart_plan={
            "chart_type": "table",
            "title": "超收数量明细",
            "x_axis": None,
            "y_axis": None,
            "sort": None,
        },
    )

    rows = _sort_table_rows(result)

    assert [row["order_no"] for row in rows] == ["CG752614", "CG752610"]
