"""Generate a Power BI PBIR page from a completed AI analysis.

This module writes only the generated ``AI分析`` page and its visuals. Existing
report pages remain untouched. Visuals are bound to the project's semantic
model, while returned dimension values are added as categorical filters so a
ranking result such as Top 5 remains faithful to the AI result.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ai.analysis_result import AnalysisResult


AI_PAGE_ID = "f0a1b2c3d4e5"
AI_PAGE_DISPLAY_NAME = "AI分析"
AI_CHART_VISUAL_ID = "f0a1b2c3d4e6"
AI_TABLE_VISUAL_ID = "f0a1b2c3d4e7"

_METRIC_BINDINGS = {
    "purchase_amount": ("supply_chain_ai purchase_detail", "采购金额"),
    "purchase_qty": ("supply_chain_ai purchase_detail", "采购数量"),
    "received_qty": ("supply_chain_ai purchase_detail", "累计收货数量"),
    "over_receipt_qty": ("supply_chain_ai purchase_detail", "超收数量"),
    "unreceived_qty": ("supply_chain_ai purchase_detail", "未收数量"),
    "purchase_order_count": ("supply_chain_ai purchase_detail", "采购订单数"),
    "supplier_count": ("supply_chain_ai purchase_detail", "供应商数"),
    "material_count": ("supply_chain_ai purchase_detail", "物料种类数"),
    "receipt_rate": ("supply_chain_ai purchase_detail", "收货率"),
    "weighted_unit_price": ("supply_chain_ai purchase_detail", "加权采购单价"),
}

_DIMENSION_BINDINGS = {
    "supplier": ("supply_chain_ai supplier", "supplier_name", "supplier_name"),
    "supplier_name": ("supply_chain_ai supplier", "supplier_name", "supplier_name"),
    "material": ("supply_chain_ai purchase_detail", "material_name", "material_name"),
    "material_name": ("supply_chain_ai purchase_detail", "material_name", "material_name"),
    "order_date": ("supply_chain_ai purchase_detail", "order_date", "order_date"),
    "date": ("supply_chain_ai purchase_detail", "order_date", "order_date"),
    "warehouse_date": ("supply_chain_ai purchase_detail", "warehouse_date", "warehouse_date"),
    "order_no": ("supply_chain_ai purchase_detail", "order_no", "order_no"),
}


def build_ai_page_from_payload(
    payload: AnalysisResult | Mapping[str, Any],
    report_root: str | Path,
    *,
    page_id: str = AI_PAGE_ID,
) -> Path:
    """Create or update the generated AI page and return its directory."""

    data = payload.to_dict() if isinstance(payload, AnalysisResult) else dict(payload)
    plan = data.get("analysis_plan") or {}
    chart_plan = data.get("chart_plan") or {}
    rows = data.get("rows") or []

    metric = plan.get("metric") or chart_plan.get("y_axis")
    metric_binding = _METRIC_BINDINGS.get(metric)
    if not metric_binding:
        raise ValueError(f"无法将指标映射到 Power BI 度量值：{metric}")

    dimension_key = plan.get("dimension") or chart_plan.get("x_axis")
    dimension_binding = _DIMENSION_BINDINGS.get(dimension_key)

    pages_root = Path(report_root).expanduser() / "definition" / "pages"
    pages_path = pages_root / "pages.json"
    if not pages_path.exists():
        raise FileNotFoundError(f"找不到 Power BI 页面目录：{pages_path}")

    page_root = pages_root / page_id
    visuals_root = page_root / "visuals"
    visuals_root.mkdir(parents=True, exist_ok=True)

    page_title = str(chart_plan.get("title") or data.get("question") or "AI分析")
    page_document = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": page_id,
        "displayName": AI_PAGE_DISPLAY_NAME,
        "displayOption": "FitToPage",
        "height": 1080,
        "width": 1920,
    }
    _write_json(page_root / "page.json", page_document)

    if dimension_binding:
        chart_document = _build_dimension_chart(
            chart_plan=chart_plan,
            title=page_title,
            dimension=dimension_binding,
            metric=metric_binding,
            rows=rows,
        )
        table_document = _build_dimension_table(
            title=page_title,
            dimension=dimension_binding,
            metric=metric_binding,
            rows=rows,
        )
        _write_json(
            visuals_root / AI_CHART_VISUAL_ID / "visual.json",
            chart_document,
        )
        _write_json(
            visuals_root / AI_TABLE_VISUAL_ID / "visual.json",
            table_document,
        )
    else:
        card_document = _build_card(title=page_title, metric=metric_binding)
        _write_json(
            visuals_root / AI_CHART_VISUAL_ID / "visual.json",
            card_document,
        )

    pages_document = json.loads(pages_path.read_text(encoding="utf-8"))
    page_order = list(pages_document.get("pageOrder") or [])
    if page_id not in page_order:
        page_order.append(page_id)
    pages_document["pageOrder"] = page_order
    pages_document["activePageName"] = page_id
    _write_json(pages_path, pages_document)
    return page_root


def _build_dimension_chart(
    *,
    chart_plan: Mapping[str, Any],
    title: str,
    dimension: tuple[str, str, str],
    metric: tuple[str, str],
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    chart_type = str(chart_plan.get("chart_type") or "bar_chart")
    visual_type = {
        "bar_chart": "barChart",
        "bar": "barChart",
        "column_chart": "columnChart",
        "column": "columnChart",
        "line_chart": "lineChart",
        "line": "lineChart",
    }.get(chart_type, "barChart")
    category_slot = "Category"
    value_slot = "Y"
    query_state = {
        category_slot: {
            "projections": [
                {"field": _column_field(dimension), "queryRef": _query_ref(dimension)}
            ]
        },
        value_slot: {
            "projections": [
                {"field": _measure_field(metric), "queryRef": _query_ref(metric)}
            ]
        },
    }
    document = _visual_base(
        visual_id=AI_CHART_VISUAL_ID,
        visual_type=visual_type,
        position={"x": 40, "y": 40, "z": 0, "width": 1840, "height": 500},
        title=title,
        query_state=query_state,
    )
    return document


def _build_dimension_table(
    *,
    title: str,
    dimension: tuple[str, str, str],
    metric: tuple[str, str],
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    query_state = {
        "Rows": {
            "projections": [
                {
                    "field": _column_field(dimension),
                    "queryRef": _query_ref(dimension),
                    "active": True,
                }
            ]
        },
        "Values": {
            "projections": [
                {"field": _measure_field(metric), "queryRef": _query_ref(metric)}
            ]
        },
    }
    document = _visual_base(
        visual_id=AI_TABLE_VISUAL_ID,
        visual_type="pivotTable",
        position={"x": 40, "y": 580, "z": 0, "width": 1840, "height": 420},
        title=f"{title}（明细）",
        query_state=query_state,
    )
    return document


def _build_card(*, title: str, metric: tuple[str, str]) -> dict[str, Any]:
    return _visual_base(
        visual_id=AI_CHART_VISUAL_ID,
        visual_type="card",
        position={"x": 40, "y": 40, "z": 0, "width": 600, "height": 260},
        title=title,
        query_state={
            "Values": {
                "projections": [
                    {"field": _measure_field(metric), "queryRef": _query_ref(metric)}
                ]
            }
        },
    )


def _visual_base(
    *,
    visual_id: str,
    visual_type: str,
    position: dict[str, int],
    title: str,
    query_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json",
        "name": visual_id,
        "position": position,
        "visual": {
            "visualType": visual_type,
            "query": {"queryState": query_state},
            "visualContainerObjects": {
                "title": [
                    {
                        "properties": {
                            "text": {
                                "expr": {"Literal": {"Value": _literal(title)}}
                            },
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                        }
                    }
                ]
            },
            "drillFilterOtherVisuals": True,
        },
    }


def _column_field(binding: tuple[str, str, str]) -> dict[str, Any]:
    entity, prop, _ = binding
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def _measure_field(binding: tuple[str, str]) -> dict[str, Any]:
    entity, prop = binding
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def _query_ref(binding: tuple[str, ...]) -> str:
    return f"{binding[0]}.{binding[1]}"


def _dimension_filter(
    binding: tuple[str, str, str],
    rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    entity, prop, row_key = binding
    values = []
    seen = set()
    for row in rows:
        value = row.get(row_key)
        if value is None or value in seen:
            continue
        seen.add(value)
        values.append(value)
    if not values:
        return []

    source_alias = "ai"
    return [
        {
            "name": "AIResultDimensionFilter",
            "expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": prop,
                }
            },
            "filter": {
                "Version": 2,
                "From": [{"Name": source_alias, "Entity": entity, "Type": 0}],
                "Where": [
                    {
                        "Condition": {
                            "In": {
                                "Expressions": [
                                    {
                                        "Column": {
                                            "Expression": {
                                                "SourceRef": {"Source": source_alias}
                                            },
                                            "Property": prop,
                                        }
                                    }
                                ],
                                "Values": [[{"Literal": {"Value": _literal_value(value)}}] for value in values],
                            }
                        }
                    }
                ],
            },
            "type": "Categorical",
        }
    ]


def _literal(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _literal_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _literal(str(value))


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
