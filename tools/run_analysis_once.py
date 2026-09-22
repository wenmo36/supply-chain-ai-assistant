"""Run one natural-language analysis end to end.

This is a non-interactive entry point for scripts, PowerShell wrappers, and a
future web chat UI. It keeps the existing interactive ``main.py`` unchanged.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.agent import run_analysis
from config.logging_config import configure_logging
from config.settings import (
    POWERBI_AUTO_BUILD,
    POWERBI_REPORT_ROOT,
    POWERBI_RESULT_PATH,
)
from errors import format_user_error
from integrations.powerbi_adapter import write_powerbi_payload
from integrations.powerbi_report_builder import build_ai_page_from_payload
from visualization.renderer import render


def run_once(question: str):
    """Run one analysis and return its standard ``AnalysisResult``."""

    if not question or not question.strip():
        raise ValueError("分析问题不能为空")

    result = run_analysis(question.strip())

    if POWERBI_RESULT_PATH:
        path = write_powerbi_payload(result, POWERBI_RESULT_PATH)
        print(f"Power BI JSON 已更新：{path.resolve()}")

    if POWERBI_AUTO_BUILD:
        page_path = build_ai_page_from_payload(result, POWERBI_REPORT_ROOT)
        print(f"Power BI AI 页面已更新：{page_path.resolve()}")

    if result.rows:
        chart_path = render(result)
        print(f"PNG 图表已生成：{chart_path.resolve()}")
    else:
        print("查询结果为空，未生成 PNG 图表。")

    print("\n--- Analysis Plan ---")
    print(json.dumps(result.analysis_plan, ensure_ascii=False, indent=2))
    print("\n--- SQL ---")
    print(result.sql)
    print("\n--- 查询结果 ---")
    print(json.dumps(result.to_dict()["rows"], ensure_ascii=False, indent=2))
    print(f"\nSQL 修复次数：{result.repair_count}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="执行一次供应链 AI 分析")
    parser.add_argument(
        "question",
        nargs="?",
        help="自然语言问题；不传时进入一次性输入模式",
    )
    args = parser.parse_args()
    question = args.question or input("请输入分析问题：").strip()

    configure_logging()
    logger = logging.getLogger(__name__)
    try:
        run_once(question)
        return 0
    except Exception as error:
        logger.exception("One-shot analysis failed")
        print("\n错误：", format_user_error(error))
        print("详细日志：logs/app.log")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
