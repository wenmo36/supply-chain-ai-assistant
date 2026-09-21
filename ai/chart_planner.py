"""
AI 图表规划模块

职责：
1. 根据 Analysis Plan 判断合适的图表类型
2. 确定 X / Y 轴
3. 生成标准化图表配置
4. 不负责绘图
5. 不负责 Power BI 执行
"""

import json

from openai import OpenAI

from config.settings import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_TIMEOUT_SECONDS,
    AI_MAX_RETRIES
)

from semantic.metrics import METRICS
from semantic.dimensions import DIMENSIONS


def _get_client() -> OpenAI:
    """Create the API client only when a model call is required."""

    return OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        timeout=AI_TIMEOUT_SECONDS,
        max_retries=AI_MAX_RETRIES
    )


CHART_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "chart_type": {
            "type": "string",
            "enum": [
                "bar_chart",
                "column_chart",
                "line_chart",
                "table",
                "card"
            ]
        },
        "title": {
            "type": "string"
        },
        "x_axis": {
            "type": ["string", "null"]
        },
        "y_axis": {
            "type": ["string", "null"]
        },
        "sort": {
            "type": ["string", "null"],
            "enum": ["asc", "desc", None]
        },
        "orientation": {
            "type": ["string", "null"],
            "enum": ["horizontal", "vertical", None]
        },
        "show_data_labels": {
            "type": "boolean"
        }
    },
    "required": [
        "chart_type",
        "title",
        "x_axis",
        "y_axis",
        "sort",
        "orientation",
        "show_data_labels"
    ],
    "additionalProperties": False
}


CHART_SYSTEM_PROMPT = """
你是一名企业级 BI 可视化规划专家。

你的任务是：
根据 Analysis Plan，为当前分析结果生成标准化 Chart Plan。

你不负责：
- 生成 SQL
- 执行 SQL
- 创建 Power BI
- 修改数据库

你只负责决定“数据应该如何可视化”。

规则：

1. ranking + entity dimension
   优先使用 bar_chart。

2. trend
   优先使用 line_chart。

3. filter
   如果结果是多个明细记录，优先使用 table。

4. summary
   单一核心指标优先使用 card。

5. 排名数据通常按降序展示。

6. 时间趋势：
   X 轴应该是时间维度，
   Y 轴应该是指标。

7. 排名：
   X 轴应该是维度，
   Y 轴应该是指标。

8. 表格：
   可以设置 x_axis / y_axis 为 null。

9. 只能使用提供的 metric / dimension。
10. 不要虚构字段。
11. 只输出 JSON。
"""


def build_chart_plan(
    analysis_plan: dict
) -> dict:
    """
    根据 Analysis Plan 生成 Chart Plan。
    """

    if not analysis_plan:
        raise ValueError("Analysis Plan 不能为空")

    context = {
        "analysis_plan": analysis_plan,
        "metrics": METRICS,
        "dimensions": DIMENSIONS
    }

    response = _get_client().chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": CHART_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": json.dumps(
                    context,
                    ensure_ascii=False,
                    indent=2
                )
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "chart_plan",
                "strict": True,
                "schema": CHART_PLAN_SCHEMA
            }
        },
        temperature=0
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("AI 未返回 Chart Plan")

    return json.loads(content)
