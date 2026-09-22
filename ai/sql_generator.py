"""
企业级 SQL 生成模块

职责：
1. 接收 Analysis Plan
2. 读取数据库真实 Schema
3. 读取业务指标、维度和业务规则
4. 生成标准化只读 SQL

注意：
本模块只负责生成 SQL。
不负责执行 SQL。
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

from database.schema import get_schema

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


SQL_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {
            "type": "string"
        }
    },
    "required": [
        "sql"
    ],
    "additionalProperties": False
}


SQL_SYSTEM_PROMPT = """
你是一名企业级供应链 BI SQL 专家。

你的任务是：
根据 Analysis Plan、数据库真实 Schema、业务指标定义、
分析维度和业务规则，生成一条正确的 MySQL 只读 SQL。

你只能生成 SQL。
不要执行 SQL。
不要解释 SQL。
不要输出 Markdown。
不要输出 ```sql。
只返回符合 JSON Schema 的结果。

====================
核心原则
====================

1. 必须严格使用数据库真实存在的表和字段。

2. 必须严格按照 metric 定义计算指标。
   如果 Analysis Plan 中存在 metrics 列表且包含多个指标，
   必须在同一条 SQL 中为每个指标生成一列，列别名必须使用对应的
   语义键（例如 purchase_amount、receipt_rate、unreceived_qty）。

3. 必须按照正确的事实粒度进行聚合。

4. 如果存在 1:N JOIN 风险，
   不允许直接聚合可能被重复展开的父表指标。

5. 涉及多个事实粒度时：
   先分别聚合，再 JOIN。

6. 采购金额：
   purchase_qty * unit_price

7. 采购数量：
   purchase_qty

8. 收料数量：
   received_qty

   收货率必须使用：
   SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) * 100
   不要省略安全除零处理；也可以使用
   CASE WHEN SUM(purchase_qty) = 0 THEN 0 ELSE ... END。

9. 超收数量：
   - 如果按订单筛选/排名，必须先按 order_no 聚合，
     使用 SUM(received_qty) > SUM(purchase_qty) 的 HAVING 条件。
   - 如果按供应商、物料等其他维度比较，必须在目标维度汇总安全的
     超收差额，或先完成订单级聚合后再汇总到目标维度；不要强制把
     order_no 暴露为最终分组字段。
   - 不要把供应商级 over_receipt_qty 聚合结果回连到 purchase_detail
     后再次 SUM，否则会按明细行数重复累计。应将各个供应商级 CTE
     直接按 supplier_id JOIN。

10. 只允许 SELECT 或 WITH 开头的查询。

11. 禁止：
    INSERT
    UPDATE
    DELETE
    DROP
    ALTER
    TRUNCATE
    CREATE
    REPLACE
    GRANT
    REVOKE
    CALL
    LOAD DATA
    INTO OUTFILE

12. 不允许虚构表、字段或关系。

13. 对排名问题：
    使用 ORDER BY + LIMIT。

14. 对供应商：
    supplier.supplier_id
    = purchase_detail.supplier_id

15. 所有非聚合字段必须正确出现在 GROUP BY 中。

16. 必须严格使用 Analysis Plan 中的 date_from、date_to 和 filters。

17. 日期范围使用闭区间：
    date_field >= date_from AND date_field <= date_to。

18. 时间趋势必须按 time_granularity 生成 period：
    day: DATE(date_field)
    month: DATE_FORMAT(date_field, '%Y-%m')
    quarter: CONCAT(YEAR(date_field), '-Q', QUARTER(date_field))
    year: YEAR(date_field)
    该表达式统一使用别名 period，并按 period 升序排序。

19. filters 中的字段必须通过 dimension 定义映射到真实字段。
    contains 使用 LIKE，不允许把用户输入解释为 SQL 代码。

20. 指标公式以 metrics 中的 sql_expression 为准，
    包括去重计数、未收数量、收货率和加权采购单价。

21. summary 且 dimension 为 null 时，只返回一个汇总结果，
    不得选择或 GROUP BY 日期、供应商、订单或物料字段。

22. comparison 必须按照 dimension 分组。

23. 未收数量 ranking / filter 必须排除未收数量等于 0 的分组，
    优先通过 HAVING unreceived_qty > 0 实现。

24. 禁止使用 MySQL 保留字作为别名，包括：
    order、group、select、from、where、having、limit、join、by。
    采购订单字段应直接使用 order_no，不要写 AS order。

25. 多指标 comparison 必须共享同一个 dimension GROUP BY，
    不要拆成多条 SQL，也不要遗漏 Analysis Plan.metrics 中的指标。

====================
业务语义优先于 SQL 简洁性
====================

SQL 首先必须业务正确，
其次才考虑简洁。

如果一个写法虽然语法正确，
但是可能造成指标重复，
必须选择更安全的写法。
"""


def _build_context(analysis_plan: dict) -> str:
    """
    构造 SQL 生成所需的完整上下文。
    """

    context = {
        "analysis_plan": analysis_plan,
        "database_schema": get_schema(),
        "metrics": METRICS,
        "dimensions": DIMENSIONS,
        "business_rules": BUSINESS_RULES
    }

    return json.dumps(
        context,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str
    )


def generate_sql(analysis_plan: dict) -> str:
    """
    根据 Analysis Plan 生成 SQL。
    """

    if not analysis_plan:
        raise ValueError("Analysis Plan 不能为空")

    user_prompt = f"""
请根据下面的 Analysis Plan 和企业业务上下文生成 MySQL SQL。

{_build_context(analysis_plan)}
"""

    response = _get_client().chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": SQL_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "sql_generation",
                "strict": True,
                "schema": SQL_SCHEMA
            }
        },
        temperature=0,
        max_completion_tokens=AI_MAX_OUTPUT_TOKENS
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("AI 未返回 SQL")

    result = json.loads(content)

    sql = result.get("sql")

    if not sql:
        raise ValueError("AI 返回结果中没有 SQL")

    return sql.strip()
