"""
SQL 业务风险检查器

职责：
1. 调用只读 SQL 安全检查
2. 检查指标公式是否符合语义定义
3. 检查关键分析是否使用正确粒度
4. 为后续 1:N JOIN 风险检测提供入口

注意：
这里只负责检查，不执行 SQL。
"""

import re

from tools.sql_checker import validate_sql
from semantic.metrics import METRICS
from semantic.business_rules import BUSINESS_RULES


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

    允许：
        purchase_qty * unit_price

    以及带表别名的：
        pd.purchase_qty * pd.unit_price
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

    # 允许带表别名
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

    if (
        "having" not in normalized
        or "received_qty" not in normalized
        or "purchase_qty" not in normalized
    ):
        errors.append(
            "超收检查失败："
            "必须通过 HAVING 判断超收"
        )


def _check_purchase_grain(
    sql: str,
    errors: list[str]
) -> None:
    """
    检查采购事实是否使用 purchase_detail。
    """

    normalized = _normalize_sql(sql)

    if "purchase_detail" not in normalized:
        errors.append(
            "采购指标检查失败："
            "未使用 purchase_detail"
        )


def _check_join_risk(
    sql: str,
    errors: list[str]
) -> None:
    """
    第一阶段的 JOIN 风险检查。

    当前数据库只有：
    purchase_detail
    supplier

    supplier 是采购事实的维度表，
    purchase_detail -> supplier 为 N:1，
    属于当前已知安全 JOIN。

    后续增加 receipt_detail 等事实表后，
    这里会扩展为真正的 1:N 聚合风险检测。
    """

    normalized = _normalize_sql(sql)

    if "join" not in normalized:
        return

    has_purchase_detail = "purchase_detail" in normalized
    has_supplier = "supplier" in normalized

    if has_purchase_detail and has_supplier:
        return

    errors.append(
        "JOIN 风险检查："
        "发现当前业务规则之外的 JOIN，"
        "需要人工确认是否存在 1:N 聚合风险"
    )


def validate_business_sql(
    sql: str,
    analysis_plan: dict
) -> None:
    """
    对生成 SQL 执行企业业务规则检查。

    检查失败时抛出 ValueError。
    """

    # 第一层：只读安全检查
    validate_sql(sql)

    errors = []

    metric = analysis_plan.get("metric")

    if metric == "purchase_amount":
        _check_purchase_grain(sql, errors)
        _check_purchase_amount(sql, errors)

    elif metric == "over_receipt_qty":
        _check_purchase_grain(sql, errors)
        _check_over_receipt(sql, errors)

    else:
        metric_info = METRICS.get(metric)

        if metric_info is None:
            errors.append(
                f"未知指标：{metric}"
            )

    _check_join_risk(sql, errors)

    if errors:
        raise ValueError(
            "SQL 业务规则检查失败：\n"
            + "\n".join(
                f"- {error}"
                for error in errors
            )
        )