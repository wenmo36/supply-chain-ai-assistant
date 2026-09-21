"""
V2 供应链 AI 分析 Agent

完整流程：

自然语言
    ↓
Intent
    ↓
SQL Generation
    ↓
SQL Validation
    ↓
SQL Repair（失败时）
    ↓
再次 Validation
    ↓
MySQL
"""

from ai.intent import parse_intent
from ai.chart_planner import build_chart_plan
from ai.analysis_result import AnalysisResult
from ai.sql_generator import generate_sql
from ai.sql_repair import repair_sql

from database.query import run_readonly_sql

from tools.sql_risk_checker import validate_business_sql


MAX_REPAIR_ATTEMPTS = 2


def run_analysis(question: str) -> AnalysisResult:
    """
    执行完整的 AI 数据分析流程。

    返回：
    {
        "question": 用户问题,
        "analysis_plan": Analysis Plan,
        "sql": 最终 SQL,
        "repair_count": 修复次数,
        "rows": 数据结果
    }
    """

    if not question or not question.strip():
        raise ValueError("分析问题不能为空")

    # ==========================================
    # 1. 自然语言 → Analysis Plan
    # ==========================================

    analysis_plan = parse_intent(question)

    # ==========================================
    # 2. Analysis Plan → SQL
    # ==========================================

    sql = generate_sql(analysis_plan)

    repair_count = 0

    # ==========================================
    # 3. SQL 校验
    # 4. 失败后自动修复
    # ==========================================

    while True:

        try:

            validate_business_sql(
                sql,
                analysis_plan
            )

            break

        except ValueError as error:

            repair_count += 1

            if repair_count > MAX_REPAIR_ATTEMPTS:
                raise ValueError(
                    "SQL 连续修复失败，"
                    "系统拒绝执行该 SQL。\n"
                    f"最后一次错误：{error}"
                )

            repaired = repair_sql(
                sql=sql,
                analysis_plan=analysis_plan,
                error_message=str(error)
            )

            sql = repaired["sql"]

    # ==========================================
    # 5. 通过全部检查后执行
    # ==========================================

    rows = run_readonly_sql(sql)

    chart_plan = build_chart_plan(
        analysis_plan
    )

    return AnalysisResult(
        question=question,
        analysis_plan=analysis_plan,
        sql=sql,
        rows=rows,
        chart_plan=chart_plan,
        repair_count=repair_count
    )
