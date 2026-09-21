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
    AI_MODEL
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
        base_url=AI_BASE_URL
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
                    indent=2,
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
        temperature=0
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
