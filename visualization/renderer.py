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
    figsize: tuple[int, int] = (10, 6)
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
        )
    )

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
        values
    )

    ax.set_xlabel(
        result.chart_plan["y_axis"]
    )

    ax.set_ylabel(
        result.chart_plan["x_axis"]
    )

    if result.chart_plan.get(
        "show_data_labels",
        False
    ):
        for index, value in enumerate(values):

            ax.text(
                value,
                index,
                f" {value}",
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
        values
    )

    ax.set_xlabel(
        result.chart_plan["x_axis"]
    )

    ax.set_ylabel(
        result.chart_plan["y_axis"]
    )

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
                f"{value}",
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

    ax.plot(
        labels,
        values,
        marker="o"
    )

    ax.set_xlabel(
        result.chart_plan["x_axis"]
    )

    ax.set_ylabel(
        result.chart_plan["y_axis"]
    )

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

    fig, ax = plt.subplots(
        figsize=(10, 4)
    )

    ax.axis("off")

    if not rows:

        headers = []
        data = []

    else:

        headers = list(
            rows[0].keys()
        )

        data = [
            [
                row.get(column)
                for column in headers
            ]
            for row in rows
        ]

    table = ax.table(
        cellText=data,
        colLabels=headers,
        loc="center"
    )

    table.auto_set_font_size(
        False
    )

    table.set_fontsize(
        10
    )

    table.scale(
        1,
        1.5
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
        str(value),
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