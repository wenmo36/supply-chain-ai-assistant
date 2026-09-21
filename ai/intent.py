"""
AI 意图识别模块

负责将用户的自然语言问题
转换为结构化分析计划。

当前阶段：
自然语言
    ↓
Intent
    ↓
Analysis Plan
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

from semantic.metrics import METRICS
from semantic.dimensions import DIMENSIONS
from semantic.glossary import GLOSSARY


FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "field": {
            "type": "string",
            "enum": list(DIMENSIONS.keys())
        },
        "operator": {
            "type": "string",
            "enum": [
                "eq",
                "ne",
                "gt",
                "gte",
                "lt",
                "lte",
                "contains"
            ]
        },
        "value": {
            "type": ["string", "number"]
        }
    },
    "required": [
        "field",
        "operator",
        "value"
    ],
    "additionalProperties": False
}


def _get_client() -> OpenAI:
    """Create the API client only when a model call is required."""

    return OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        timeout=AI_TIMEOUT_SECONDS,
        max_retries=AI_MAX_RETRIES
    )


INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "ranking",
                "trend",
                "comparison",
                "filter",
                "summary"
            ]
        },
        "metric": {
            "type": "string",
            "enum": list(METRICS.keys())
        },
        "dimension": {
            "type": ["string", "null"],
            "enum": [*DIMENSIONS.keys(), None]
        },
        "limit": {
            "type": ["integer", "null"]
        },
        "sort": {
            "type": ["string", "null"],
            "enum": ["asc", "desc", None]
        },
        "time_granularity": {
            "type": ["string", "null"],
            "enum": ["day", "month", "quarter", "year", None]
        },
        "period": {
            "type": ["string", "null"]
        },
        "condition": {
            "type": ["string", "null"]
        },
        "date_from": {
            "type": ["string", "null"]
        },
        "date_to": {
            "type": ["string", "null"]
        },
        "filters": {
            "type": "array",
            "items": FILTER_SCHEMA
        }
    },
    "required": [
        "intent",
        "metric",
        "dimension",
        "limit",
        "sort",
        "time_granularity",
        "period",
        "condition",
        "date_from",
        "date_to",
        "filters"
    ],
    "additionalProperties": False
}


def _build_context() -> str:
    """
    将当前语义层信息整理成 AI 的上下文。
    """

    metrics = {
        key: {
            "name": value["name"],
            "description": value["description"],
        }
        for key, value in METRICS.items()
    }
    dimensions = {
        key: {"name": value["name"], "type": value["type"]}
        for key, value in DIMENSIONS.items()
    }
    return json.dumps(
        {
            "metrics": metrics,
            "dimensions": dimensions,
            "glossary": GLOSSARY,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


INTENT_SYSTEM_PROMPT = """
你是一名企业级供应链 BI 分析助手。

你的任务不是直接编写 SQL。

你的任务是：

1. 理解用户的自然语言分析需求
2. 从提供的业务语义层中识别标准指标
3. 识别分析维度
4. 识别分析类型
5. 识别排序、TOP N、时间粒度和时间范围
6. 输出结构化 Analysis Plan

重要规则：

- 只能使用提供的 metric
- 只能使用提供的 dimension
- 不允许虚构不存在的指标或维度
- 不确定的信息使用 null
- 没有普通筛选条件时 filters 使用空数组
- 纯总计、合计、多少等 summary 问题的 dimension 使用 null
- “各供应商”“每种物料”“按订单”等分组问题使用 comparison
- 日期范围必须拆分成 YYYY-MM-DD 格式的 date_from 和 date_to
- “某年某月”应转换为该月第一天和最后一天
- filters 只表达供应商、订单、物料和日期等普通字段筛选
- 超收等指标条件仍放在 condition
- 未收数量的 ranking / filter 默认 condition 为 unreceived_qty > 0
- 不要输出 SQL
- 不要输出解释文字
- 必须严格输出 JSON

常见分析类型：

ranking
表示 TOP N、排名、最高、最低等需求。

trend
表示趋势、按日/月/季度/年度变化。

comparison
表示环比、同比、差值、变化等。

filter
表示筛选满足某条件的数据。

summary
表示总体汇总。

业务术语必须优先参考 glossary。

时间规则：

- 按日/月/季度/年分析时 intent 使用 trend
- 同时设置对应的 time_granularity
- dimension 使用问题所针对的日期维度
- 没有明确日期字段时，采购分析默认使用 order_date
"""


def parse_intent(question: str) -> dict:
    """
    将自然语言问题转换成结构化分析计划。
    """

    if not question or not question.strip():
        raise ValueError("分析问题不能为空")

    user_prompt = f"""
当前业务语义层：

{_build_context()}

用户问题：

{question}

请根据业务语义层生成 Analysis Plan。
"""

    response = _get_client().chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": INTENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "analysis_plan",
                "strict": True,
                "schema": INTENT_SCHEMA
            }
        },
        temperature=0,
        max_completion_tokens=AI_MAX_OUTPUT_TOKENS
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("AI 未返回 Analysis Plan")

    return normalize_analysis_plan(
        json.loads(content),
        question
    )


def normalize_analysis_plan(
    analysis_plan: dict,
    question: str
) -> dict:
    """Correct deterministic intent details without another model call."""

    plan = dict(analysis_plan)
    compact_question = "".join(question.split())
    grouping_cues = ("各", "每个", "每家", "按供应商", "按物料", "按订单")
    trend_cues = (
        "趋势",
        "走势",
        "变化",
        "按日",
        "按月",
        "按季度",
        "按年",
        "每日",
        "每月",
        "每季度",
        "每年",
        "逐日",
        "逐月",
    )

    if (
        plan.get("intent") == "trend"
        and not any(cue in compact_question for cue in trend_cues)
    ):
        plan["intent"] = "summary"
        plan["dimension"] = None
        plan["time_granularity"] = None

    if plan.get("intent") == "summary":
        if any(cue in compact_question for cue in grouping_cues):
            plan["intent"] = "comparison"
        else:
            plan["dimension"] = None

    if (
        plan.get("metric") == "unreceived_qty"
        and plan.get("intent") in {"ranking", "filter"}
        and not plan.get("condition")
    ):
        plan["condition"] = "unreceived_qty > 0"

    over_receipt_filter_cues = ("哪些", "哪些订单", "存在超收", "有超收")
    ranking_cues = ("最高", "最多", "排名", "top", "前")
    if (
        plan.get("metric") == "over_receipt_qty"
        and any(cue in compact_question for cue in over_receipt_filter_cues)
        and not any(cue in compact_question.lower() for cue in ranking_cues)
    ):
        plan["intent"] = "filter"
        plan["limit"] = None
        plan["sort"] = None

    return plan
