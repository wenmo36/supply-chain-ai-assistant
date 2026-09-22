"""
本地可视化渲染器

职责：
1. 接收 AnalysisResult
2. 根据 Chart Plan 选择图表类型
3. 将语义字段映射为真实查询字段
4. 生成本地 PNG 图表

不负责：
- SQL 生成
- SQL 执行
- 业务分析
- Power BI API

当前支持：
- bar_chart
- column_chart
- line_chart
- table
- card
"""

from pathlib import Path
from typing import Any

import matplotlib

# 使用无界面后端，适合：
# - 自动化测试
# - 批量生成 PNG
# - 服务器环境
# - Power BI 前置数据处理
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import StrMethodFormatter

from ai.analysis_result import AnalysisResult
from semantic.dimensions import DIMENSIONS
from semantic.metrics import METRICS


# ============================================================
# 基础配置
# ============================================================

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# 中文字体配置
# ============================================================

WINDOWS_FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
    Path(r"C:\Windows\Fonts\simsun.ttc"),
]


def _configure_chinese_font() -> str | None:
    """
    自动寻找 Windows 中文字体。

    优先级：
    1. Microsoft YaHei
    2. SimHei
    3. SimSun

    返回：
        实际使用的字体名称
    """

    for font_path in WINDOWS_FONT_CANDIDATES:

        if not font_path.exists():
            continue

        font_properties = font_manager.FontProperties(
            fname=str(font_path)
        )

        font_name = font_properties.get_name()

        plt.rcParams["font.sans-serif"] = [
            font_name
        ]

        # 避免负号显示成方框
        plt.rcParams["axes.unicode_minus"] = False

        return font_name

    return None


CHINESE_FONT = _configure_chinese_font()

FIELD_LABELS = {
    "supplier_id": "供应商ID",
    "supplier_name": "供应商",
    "order_no": "采购订单号",
    "order_date": "采购日期",
    "material_code": "物料编码",
    "material_name": "物料名称",
    "warehouse_date": "入库日期",
    "receipt_date": "收货日期",
    "period": "期间",
}


def _display_name(semantic_or_column: str | None) -> str:
    """Resolve a semantic key or SQL column to a Chinese business label."""

    if not semantic_or_column:
        return ""
    if semantic_or_column in METRICS:
        return METRICS[semantic_or_column]["name"]
    if semantic_or_column in DIMENSIONS:
        return DIMENSIONS[semantic_or_column]["name"]
    return FIELD_LABELS.get(semantic_or_column, semantic_or_column)


def _format_value(value: Any, semantic_name: str | None = None) -> str:
    """Format a value for business-facing labels."""

    if not isinstance(value, (int, float)):
        return str(value)

    unit = METRICS.get(semantic_name or "", {}).get("unit")
    decimals = 2 if isinstance(value, float) and not value.is_integer() else 0
    formatted = f"{value:,.{decimals}f}"

    if unit == "元":
        return f"¥{formatted}"
    if unit == "%":
        return f"{formatted}%"
    if unit == "元/单位":
        return f"¥{formatted}/单位"
    if unit and unit != "数量":
        return f"{formatted} {unit}"
    return formatted


def get_font_status() -> str:
    """
    返回当前 Renderer 使用的中文字体状态。
    """

    if CHINESE_FONT:
        return f"中文字体：{CHINESE_FONT}"

    return (
        "未找到可用中文字体，"
        "中文可能显示为方框"
    )


# ============================================================
# 字段解析
# ============================================================

def _resolve_column(
    rows: list[dict[str, Any]],
    semantic_name: str
) -> str:
    """
    将语义字段名称映射到查询结果中的真实字段。

    示例：

        supplier
            ↓
        supplier_name

        purchase_amount
            ↓
        purchase_amount

    支持：
    - Dimension
    - Metric
    - 查询结果已经使用语义名称作为字段名
    """

    if not rows:
        raise ValueError(
            "查询结果为空，无法解析图表字段"
        )

    available_columns = set(
        rows[0].keys()
    )

    # --------------------------------------------------------
    # 1. 查询结果中直接存在
    # --------------------------------------------------------

    if semantic_name in available_columns:
        return semantic_name

    # --------------------------------------------------------
    # 2. Dimension 映射
    # --------------------------------------------------------

    dimension = DIMENSIONS.get(
        semantic_name
    )

    if dimension:

        candidates = [
            dimension.get("label"),
            dimension.get("field"),
            dimension.get("key")
        ]

        for field_name in candidates:

            if (
                field_name
                and field_name in available_columns
            ):
                return field_name

        if (
            dimension.get("type") == "date"
            and "period" in available_columns
        ):
            return "period"

    # --------------------------------------------------------
    # 3. Metric 映射
    # --------------------------------------------------------

    metric = METRICS.get(
        semantic_name
    )

    if metric:

        if semantic_name in available_columns:
            return semantic_name

    # --------------------------------------------------------
    # 4. 无法解析
    # --------------------------------------------------------

    raise ValueError(
        f"无法将语义字段 "
        f"'{semantic_name}' "
        f"映射到查询结果字段。\n"
        f"当前字段："
        f"{list(available_columns)}"
    )


# ============================================================
# 数据提取
# ============================================================

def _get_axis_data(
    result: AnalysisResult
) -> tuple[list[str], list[Any]]:
    """
    根据 Chart Plan 获取 X / Y 轴数据。
    """

    rows = result.rows
    chart_plan = result.chart_plan

    if not rows:
        raise ValueError(
            "查询结果为空，无法生成图表"
        )

    semantic_x_axis = chart_plan.get(
        "x_axis"
    )

    semantic_y_axis = chart_plan.get(
        "y_axis"
    )

    if not semantic_x_axis:
        raise ValueError(
            "当前图表缺少 x_axis"
        )

    if not semantic_y_axis:
        raise ValueError(
            "当前图表缺少 y_axis"
        )

    x_column = _resolve_column(
        rows,
        semantic_x_axis
    )

    y_column = _resolve_column(
        rows,
        semantic_y_axis
    )

    labels = [
        str(row[x_column])
        for row in rows
    ]

    values = [
        row[y_column]
        for row in rows
    ]

    return labels, values


# ============================================================
# 输出文件
# ============================================================

def _build_output_path(
    result: AnalysisResult
) -> Path:
    """
    根据图表标题生成安全输出文件名。
    """

    title = result.chart_plan.get(
        "title",
        "chart"
    )

    invalid_chars = (
        "\\",
        "/",
        ":",
        "*",
        "?",
        '"',
        "<",
        ">",
        "|"
    )

    safe_name = title

    for char in invalid_chars:
        safe_name = safe_name.replace(
            char,
            "_"
        )

    return OUTPUT_DIR / (
        f"{safe_name}.png"
    )


# ============================================================
# Figure 初始化
# ============================================================

def _create_figure(
    result: AnalysisResult,
    figsize: tuple[int, int] = (9, 5.5)
):
    """
    创建统一 Figure / Axes。
    """

    fig, ax = plt.subplots(
        figsize=figsize
    )

    ax.set_title(
        result.chart_plan.get(
            "title",
            ""
        ),
        fontsize=15,
        pad=14
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig, ax


# ============================================================
# Bar Chart
# ============================================================

def _render_bar_chart(
    result: AnalysisResult,
    output_path: Path
) -> Path:

    labels, values = _get_axis_data(
        result
    )

    fig, ax = _create_figure(
        result
    )

    ax.barh(
        labels,
        values,
        color="#287EB8"
    )

    ax.set_xlabel(
        _display_name(result.chart_plan["y_axis"])
    )

    ax.set_ylabel(
        _display_name(result.chart_plan["x_axis"])
    )

    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)

    if result.chart_plan.get("sort") == "desc":
        ax.invert_yaxis()

    if result.chart_plan.get(
        "show_data_labels",
        False
    ):
        for index, value in enumerate(values):

            ax.text(
                value,
                index,
                f"  {_format_value(value, result.chart_plan['y_axis'])}",
                va="center"
            )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output_path


# ============================================================
# Column Chart
# ============================================================

def _render_column_chart(
    result: AnalysisResult,
    output_path: Path
) -> Path:

    labels, values = _get_axis_data(
        result
    )

    fig, ax = _create_figure(
        result
    )

    ax.bar(
        labels,
        values,
        color="#287EB8"
    )

    ax.set_xlabel(
        _display_name(result.chart_plan["x_axis"])
    )

    ax.set_ylabel(
        _display_name(result.chart_plan["y_axis"])
    )

    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)

    ax.tick_params(
        axis="x",
        labelrotation=30
    )

    if result.chart_plan.get(
        "show_data_labels",
        False
    ):
        for index, value in enumerate(values):

            ax.text(
                index,
                value,
                _format_value(value, result.chart_plan["y_axis"]),
                ha="center",
                va="bottom"
            )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output_path


# ============================================================
# Line Chart
# ============================================================

def _render_line_chart(
    result: AnalysisResult,
    output_path: Path
) -> Path:

    labels, values = _get_axis_data(
        result
    )

    fig, ax = _create_figure(
        result
    )

    # Keep the renderer faithful to Chart Plan.  A single time bucket is
    # still a line-chart result; silently changing it to a bar chart makes
    # the local PNG disagree with the Power BI visual.
    ax.plot(
        labels,
        values,
        marker="o",
        color="#287EB8"
    )

    if len(labels) == 1:
        ax.annotate(
            _format_value(values[0], result.chart_plan["y_axis"]),
            (0, values[0]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
        )

    ax.set_xlabel(
        _display_name(result.chart_plan["x_axis"])
    )

    ax.set_ylabel(
        _display_name(result.chart_plan["y_axis"])
    )

    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)

    ax.tick_params(
        axis="x",
        labelrotation=30
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output_path


# ============================================================
# Table
# ============================================================

def _render_table(
    result: AnalysisResult,
    output_path: Path
) -> Path:

    rows = result.rows

    row_count = max(len(rows), 1)
    fig_height = min(max(2.2 + row_count * 0.45, 3.2), 10)
    fig, ax = plt.subplots(figsize=(9, fig_height))

    ax.axis("off")

    if not rows:

        headers = []
        data = []

    else:

        columns = list(
            rows[0].keys()
        )
        headers = [_display_name(column) for column in columns]

        data = [
            [
                _format_value(row.get(column), column)
                for column in columns
            ]
            for row in rows
        ]

    table = ax.table(
        cellText=data,
        colLabels=headers,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        10
    )

    table.scale(
        1,
        1.4
    )

    for (row, _column), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#287EB8")
            cell.set_text_props(color="white", weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#F3F6F8")

    ax.set_title(
        result.chart_plan.get(
            "title",
            ""
        )
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output_path


# ============================================================
# Card
# ============================================================

def _render_card(
    result: AnalysisResult,
    output_path: Path
) -> Path:

    rows = result.rows

    if not rows:

        value = "N/A"

    else:

        first_row = rows[0]

        if len(first_row) == 1:

            value = next(
                iter(
                    first_row.values()
                )
            )

        else:

            value = list(
                first_row.values()
            )[-1]

    fig, ax = plt.subplots(
        figsize=(8, 4)
    )

    ax.axis("off")

    ax.text(
        0.5,
        0.5,
        _format_value(value, result.analysis_plan.get("metric")),
        ha="center",
        va="center",
        fontsize=32
    )

    ax.set_title(
        result.chart_plan.get(
            "title",
            ""
        )
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close(fig)

    return output_path


# ============================================================
# Renderer 注册表
# ============================================================

RENDERERS = {
    "bar_chart": _render_bar_chart,
    "column_chart": _render_column_chart,
    "line_chart": _render_line_chart,
    "table": _render_table,
    "card": _render_card
}


# ============================================================
# 主入口
# ============================================================

def render(
    result: AnalysisResult
) -> Path:
    """
    根据 Chart Plan 自动选择对应 Renderer。

    返回：
        PNG 文件路径
    """

    if not isinstance(
        result,
        AnalysisResult
    ):
        raise TypeError(
            "render() 必须接收 AnalysisResult"
        )

    chart_type = result.chart_plan.get(
        "chart_type"
    )

    if chart_type not in RENDERERS:

        raise ValueError(
            f"不支持的图表类型："
            f"{chart_type}"
        )

    output_path = _build_output_path(
        result
    )

    renderer = RENDERERS[
        chart_type
    ]

    return renderer(
        result,
        output_path
    )
