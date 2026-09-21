"""
SQL 业务风险检查器

职责：
1. SQL 只读安全检查
2. 指标公式检查
3. 指标事实粒度检查
4. 基于数据库外键关系检查 JOIN 风险
5. 为后续 Grain-Aware SQL Validation 提供基础
"""

import re

from tools.sql_checker import validate_sql

from database.schema import get_relationships

from semantic.metrics import METRICS
from semantic.dimensions import DIMENSIONS


def _normalize_sql(sql: str) -> str:
    """
    统一 SQL 格式，方便规则检查。
    """

    return re.sub(
        r"\s+",
        " ",
        sql.strip().rstrip(";")
    ).lower()


def _check_purchase_amount(
    sql: str,
    errors: list[str]
) -> None:
    """
    检查采购金额公式。
    """

    normalized = _normalize_sql(sql)

    if "purchase_qty" not in normalized:
        errors.append(
            "采购金额检查失败：SQL 未使用 purchase_qty"
        )

    if "unit_price" not in normalized:
        errors.append(
            "采购金额检查失败：SQL 未使用 unit_price"
        )

    purchase_amount_pattern = re.compile(
        r"(?:\b\w+\.)?purchase_qty"
        r"\s*\*\s*"
        r"(?:\b\w+\.)?unit_price",
        re.IGNORECASE
    )

    if not purchase_amount_pattern.search(normalized):
        errors.append(
            "采购金额检查失败："
            "必须使用 purchase_qty * unit_price 计算"
        )


def _check_over_receipt(
    sql: str,
    errors: list[str]
) -> None:
    """
    检查订单超收规则。
    """

    normalized = _normalize_sql(sql)

    if "group by order_no" not in normalized:
        errors.append(
            "超收检查失败："
            "订单层超收必须 GROUP BY order_no"
        )

    if "sum(received_qty)" not in normalized:
        errors.append(
            "超收检查失败："
            "缺少 SUM(received_qty)"
        )

    if "sum(purchase_qty)" not in normalized:
        errors.append(
            "超收检查失败："
            "缺少 SUM(purchase_qty)"
        )

    if "having" not in normalized:
        errors.append(
            "超收检查失败："
            "必须通过 HAVING 判断超收"
        )


def _check_extended_metric(
    sql: str,
    metric: str,
    errors: list[str]
) -> None:
    normalized = _normalize_sql(sql)
    qualified = r"(?:\b\w+\.)?"

    count_fields = {
        "purchase_order_count": "order_no",
        "supplier_count": "supplier_id",
        "material_count": "material_code",
    }
    if metric in count_fields:
        field = count_fields[metric]
        pattern = re.compile(
            rf"count\s*\(\s*distinct\s+{qualified}{field}\s*\)",
            re.IGNORECASE,
        )
        if not pattern.search(normalized):
            errors.append(
                f"{METRICS[metric]['name']}检查失败：必须使用 "
                f"COUNT(DISTINCT {field})"
            )

    elif metric == "unreceived_qty":
        required = ("greatest", "purchase_qty", "received_qty")
        if not all(token in normalized for token in required):
            errors.append(
                "未收数量检查失败：必须使用 "
                "GREATEST(purchase_qty - received_qty, 0)"
            )

    elif metric == "receipt_rate":
        required = ("sum(", "received_qty", "purchase_qty", "nullif")
        percentage_pattern = re.compile(r"\*\s*100(?:\.0+)?\b")
        if (
            not all(token in normalized for token in required)
            or not percentage_pattern.search(normalized)
        ):
            errors.append(
                "收货率检查失败：必须使用汇总收料数量除以汇总采购数量，"
                "并通过 NULLIF 防止除零"
            )

    elif metric == "weighted_unit_price":
        required = ("purchase_qty", "unit_price", "nullif", "sum(")
        if not all(token in normalized for token in required):
            errors.append(
                "加权采购单价检查失败：必须使用采购金额除以汇总采购数量"
            )


def _check_time_analysis(
    sql: str,
    analysis_plan: dict,
    errors: list[str]
) -> None:
    if analysis_plan.get("intent") != "trend":
        return

    normalized = _normalize_sql(sql)
    granularity = analysis_plan.get("time_granularity")
    expected_tokens = {
        "day": ("date(",),
        "month": ("date_format(", "%y-%m"),
        "quarter": ("year(", "quarter("),
        "year": ("year(",),
    }

    if granularity not in expected_tokens:
        errors.append("时间趋势检查失败：缺少有效的 time_granularity")
        return

    if not all(
        token in normalized
        for token in expected_tokens[granularity]
    ):
        errors.append(
            f"时间趋势检查失败：SQL 未按 {granularity} 粒度聚合"
        )

    if " period" not in normalized:
        errors.append("时间趋势检查失败：时间表达式必须使用别名 period")

    if "order by" not in normalized:
        errors.append("时间趋势检查失败：必须按 period 排序")


def _check_plan_filters(
    sql: str,
    analysis_plan: dict,
    errors: list[str]
) -> None:
    normalized = _normalize_sql(sql)

    for key in ("date_from", "date_to"):
        value = analysis_plan.get(key)
        if value and str(value).lower() not in normalized:
            errors.append(f"筛选检查失败：SQL 遗漏 {key}={value}")

    for item in analysis_plan.get("filters") or []:
        field = item.get("field")
        value = item.get("value")
        dimension = DIMENSIONS.get(field, {})
        candidates = {
            field,
            dimension.get("key"),
            dimension.get("label"),
            dimension.get("field"),
        }
        candidates.discard(None)

        if not any(str(candidate).lower() in normalized for candidate in candidates):
            errors.append(f"筛选检查失败：SQL 遗漏筛选字段 {field}")

        if value is not None and str(value).lower() not in normalized:
            errors.append(f"筛选检查失败：SQL 遗漏筛选值 {value}")

        if item.get("operator") == "contains" and " like " not in normalized:
            errors.append("筛选检查失败：contains 必须使用 LIKE")


def _check_analysis_shape(
    sql: str,
    analysis_plan: dict,
    errors: list[str]
) -> None:
    normalized = _normalize_sql(sql)
    intent = analysis_plan.get("intent")
    dimension = analysis_plan.get("dimension")
    metric = analysis_plan.get("metric")

    if intent == "summary" and dimension is None and "group by" in normalized:
        errors.append("汇总检查失败：纯 summary 查询不应包含 GROUP BY")

    if intent == "comparison" and dimension and "group by" not in normalized:
        errors.append("对比检查失败：comparison 查询必须按照维度 GROUP BY")

    if (
        metric == "unreceived_qty"
        and intent in {"ranking", "filter"}
        and not (
            ("having" in normalized and "> 0" in normalized)
            or (
                "where" in normalized
                and "purchase_qty" in normalized
                and "received_qty" in normalized
                and ">" in normalized
            )
        )
    ):
        errors.append("未收数量检查失败：排名或筛选必须排除 0 值")


def _check_purchase_grain(
    sql: str,
    metric: str,
    errors: list[str]
) -> None:
    """
    检查指标是否使用正确事实表。
    """

    metric_info = METRICS.get(metric)

    if metric_info is None:
        errors.append(
            f"未知指标：{metric}"
        )
        return

    fact_table = metric_info["fact_table"]
    normalized = _normalize_sql(sql)

    if fact_table.lower() not in normalized:
        errors.append(
            f"粒度检查失败：指标 {metric} "
            f"要求使用事实表 {fact_table}"
        )


def _get_relationships_for_sql(
    sql: str
) -> list[dict]:
    """
    找出 SQL 中涉及的数据库关系。
    """

    normalized = _normalize_sql(sql)

    relationships = get_relationships()

    matched = []

    for relationship in relationships:

        child_table = relationship["child_table"].lower()
        parent_table = relationship["parent_table"].lower()

        if (
            child_table in normalized
            and parent_table in normalized
        ):
            matched.append(relationship)

    return matched


def _check_join_cardinality(
    sql: str,
    metric: str,
    errors: list[str]
) -> None:
    """
    基于指标事实表 + 数据库关系
    检查潜在的 JOIN 聚合风险。

    当前阶段规则：

    1. 如果没有 JOIN，不检查。
    2. 指标事实表 JOIN 到父表（N:1）通常安全。
    3. 如果未来事实表作为父表被 JOIN 到 N 个子表，
       可能导致事实指标重复，需要预警。
    """

    normalized = _normalize_sql(sql)

    if "join" not in normalized:
        return

    metric_info = METRICS.get(metric)

    if metric_info is None:
        return

    fact_table = metric_info["fact_table"].lower()

    relationships = _get_relationships_for_sql(sql)

    for relationship in relationships:

        child_table = relationship["child_table"].lower()
        parent_table = relationship["parent_table"].lower()
        relation = relationship["relationship"]

        # 指标事实表是 child：
        #
        # purchase_detail N
        #        ↓
        # supplier 1
        #
        # N:1 JOIN 一般安全。
        if (
            relation == "N:1"
            and child_table == fact_table
        ):
            continue

        # 指标事实表是 parent：
        #
        # fact 1
        #      ↓
        # child N
        #
        # 如果直接 JOIN 后 SUM(fact.xxx)，
        # 可能出现指标重复。
        if (
            relation == "N:1"
            and parent_table == fact_table
        ):
            errors.append(
                f"潜在 1:N 聚合风险："
                f"指标事实表 {fact_table} "
                f"与 {child_table} 存在 1:N 关系，"
                f"请先聚合子表或确认指标粒度"
            )

        elif relation == "1:N":

            errors.append(
                f"潜在 1:N JOIN 风险："
                f"{parent_table} → {child_table}"
            )

        elif relation == "N:N":

            errors.append(
                f"高风险 JOIN："
                f"{child_table} ↔ {parent_table} 为 N:N"
            )


def validate_business_sql(
    sql: str,
    analysis_plan: dict
) -> None:
    """
    执行企业级 SQL 业务校验。
    """

    # 第一层：SQL 安全
    validate_sql(sql)

    errors = []

    metric = analysis_plan.get("metric")

    # 第二层：事实表 / 粒度
    _check_purchase_grain(
        sql,
        metric,
        errors
    )

    # 第三层：指标专属业务规则

    if metric == "purchase_amount":

        _check_purchase_amount(
            sql,
            errors
        )

    elif metric == "over_receipt_qty":

        _check_over_receipt(
            sql,
            errors
        )

    else:

        _check_extended_metric(
            sql,
            metric,
            errors
        )

    _check_time_analysis(
        sql,
        analysis_plan,
        errors
    )

    _check_plan_filters(
        sql,
        analysis_plan,
        errors
    )

    _check_analysis_shape(
        sql,
        analysis_plan,
        errors
    )

    # 第四层：JOIN 基数风险
    _check_join_cardinality(
        sql,
        metric,
        errors
    )

    if errors:
        raise ValueError(
            "SQL 业务规则检查失败：\n"
            + "\n".join(
                f"- {error}"
                for error in errors
            )
        )
