"""Deterministic chart planning without an additional paid model call."""

from semantic.dimensions import DIMENSIONS
from semantic.metrics import METRICS


def _semantic_name(registry: dict, key: str | None, fallback: str) -> str:
    if not key:
        return fallback
    return registry.get(key, {}).get("name", key)


def build_chart_plan(analysis_plan: dict) -> dict:
    """Build a stable chart plan from the normalized analysis plan."""

    if not analysis_plan:
        raise ValueError("Analysis Plan 不能为空")

    intent = analysis_plan.get("intent")
    metric = analysis_plan.get("metric")
    metrics = [
        key for key in (analysis_plan.get("metrics") or [metric])
        if key
    ]
    dimension = analysis_plan.get("dimension")
    sort = analysis_plan.get("sort")

    metric_name = _semantic_name(METRICS, metric, "指标")
    dimension_name = _semantic_name(DIMENSIONS, dimension, "维度")

    # A single-axis chart cannot faithfully communicate several measures with
    # different units (for example amount, percentage, and quantity).  Use a
    # matrix table for that case so the local PNG and Power BI render the same
    # complete result set.
    if len(metrics) > 1 and dimension:
        metric_names = "、".join(
            _semantic_name(METRICS, key, key) for key in metrics
        )
        return {
            "chart_type": "table",
            "title": f"{dimension_name}{metric_names}对比",
            "x_axis": dimension,
            "y_axis": metrics[0],
            "y_axes": metrics,
            "sort": sort or "desc",
            "orientation": None,
            "show_data_labels": False,
        }

    if intent == "ranking":
        limit = analysis_plan.get("limit")
        suffix = f"（前{limit}）" if limit else ""
        return {
            "chart_type": "bar_chart",
            "title": f"{dimension_name}{metric_name}排名{suffix}",
            "x_axis": dimension,
            "y_axis": metric,
            "y_axes": metrics,
            "sort": sort or "desc",
            "orientation": "horizontal",
            "show_data_labels": True,
        }

    if intent == "trend":
        return {
            "chart_type": "line_chart",
            "title": f"{metric_name}{dimension_name}趋势",
            "x_axis": dimension,
            "y_axis": metric,
            "y_axes": metrics,
            "sort": sort or "asc",
            "orientation": None,
            "show_data_labels": False,
        }

    if intent == "summary":
        return {
            "chart_type": "card",
            "title": metric_name,
            "x_axis": None,
            "y_axis": metric,
            "y_axes": metrics,
            "sort": None,
            "orientation": None,
            "show_data_labels": True,
        }

    if intent == "comparison":
        return {
            "chart_type": "column_chart",
            "title": f"{dimension_name}{metric_name}对比",
            "x_axis": dimension,
            "y_axis": metric,
            "y_axes": metrics,
            "sort": sort,
            "orientation": "vertical",
            "show_data_labels": True,
        }

    return {
        "chart_type": "table",
        "title": f"{metric_name}明细",
        "x_axis": None,
        "y_axis": None,
        "y_axes": metrics,
        "sort": sort,
        "orientation": None,
        "show_data_labels": False,
    }
