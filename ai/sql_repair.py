"""
SQL 自动修复模块

职责：
1. 接收已经被风险检查器拦截的 SQL
2. 接收具体的业务风险信息
3. 根据指标、粒度、Schema 和业务规则重新生成 SQL
4. 不执行 SQL
"""

import json

from openai import OpenAI

from config.settings import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_TIMEOUT_SECONDS,
    AI_MAX_RETRIES,
    AI_MAX_OUTPUT_TOKENS
)

from database.schema import (
    get_schema,
    get_relationships
)

from semantic.metrics import METRICS
from semantic.dimensions import DIMENSIONS
from semantic.business_rules import BUSINESS_RULES


def _get_client() -> OpenAI:
    """Create the API client only when a model call is required."""

    return OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        timeout=AI_TIMEOUT_SECONDS,
        max_retries=AI_MAX_RETRIES
    )


REPAIR_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {
            "type": "string"
        },
        "repair_reason": {
            "type": "string"
        }
    },
    "required": [
        "sql",
        "repair_reason"
    ],
    "additionalProperties": False
}


REPAIR_SYSTEM_PROMPT = """
你是一名企业级供应链 BI SQL 修复专家。

你的任务不是解释错误，而是修复已经被业务规则检查器拦截的 SQL。

你必须：

1. 保留原始 Analysis Plan 的业务意图。
2. 严格使用真实数据库 Schema。
3. 严格遵守指标定义和事实粒度。
4. 解决 SQL Checker 提出的业务风险。
5. 如果某个 JOIN 对最终结果没有贡献，应删除这个 JOIN。
6. 如果确实需要一对多子表数据：
   - 必须先在子表自己的粒度完成聚合；
   - 再 JOIN 到父表；
   - 不允许直接让父表指标被子表展开。
7. 不允许改变指标定义来“绕过”检查。
8. 只生成 MySQL SELECT / WITH 查询。
9. 不允许 INSERT、UPDATE、DELETE、DROP、ALTER 等写操作。
10. 输出 JSON，不输出 Markdown，不输出 ```sql。
11. 禁止使用 MySQL 保留字作为未加引号的别名；
    采购订单字段使用 order_no，不要使用 AS order。
12. 如果 Analysis Plan.metrics 包含多个指标，修复后的 SQL 必须保留
    同一维度分组，并为每个指标输出对应的语义键列别名。
13. 超收数量只有在订单维度的筛选/排名查询中才强制要求
    GROUP BY order_no 和 HAVING；供应商或物料对比应按目标维度汇总。
14. 收货率必须保留
    SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) * 100
    的安全除零公式，或使用等价的 CASE WHEN 零值保护。
15. 禁止把供应商级 over_receipt_qty 聚合结果回连到 purchase_detail
    后再次 SUM；应在 supplier_id 粒度直接 JOIN 各个汇总结果。
16. 表别名必须前后一致：purchase_detail 使用 pd，supplier 使用 sup，
    供应商汇总 CTE 使用 sa，超收汇总 CTE 使用 orq；禁止引用未声明的
    s.supplier_id。

特别注意：

例如：

purchase_detail
    1
    ↓
receipt_detail
    N

如果当前指标来自 purchase_detail：

SUM(purchase_detail.purchase_qty)

直接 JOIN receipt_detail 后可能重复计算。

安全方案可能包括：

A. 删除没有业务必要的 receipt_detail JOIN

或者：

B. 先将 receipt_detail 聚合到 purchase_detail_id，
   再 JOIN 回 purchase_detail。

必须根据实际业务需求选择。
"""


def repair_sql(
    sql: str,
    analysis_plan: dict,
    error_message: str
) -> dict:
    """
    根据业务校验错误自动修复 SQL。

    返回：
    {
        "sql": "...",
        "repair_reason": "..."
    }
    """

    if not sql.strip():
        raise ValueError("待修复 SQL 不能为空")

    if not error_message.strip():
        raise ValueError("SQL 风险信息不能为空")

    context = {
        "analysis_plan": analysis_plan,
        "original_sql": sql,
        "validation_error": error_message,
        "database_schema": get_schema(),
        "relationships": get_relationships(),
        "metrics": METRICS,
        "dimensions": DIMENSIONS,
        "business_rules": BUSINESS_RULES
    }

    response = _get_client().chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": REPAIR_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": json.dumps(
                    context,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    default=str
                )
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "sql_repair",
                "strict": True,
                "schema": REPAIR_SCHEMA
            }
        },
        temperature=0,
        max_completion_tokens=AI_MAX_OUTPUT_TOKENS
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("AI 未返回修复结果")

    result = json.loads(content)

    repaired_sql = result.get("sql")

    if not repaired_sql:
        raise ValueError("AI 修复结果中没有 SQL")

    return {
        "sql": repaired_sql.strip(),
        "repair_reason": result["repair_reason"]
    }
