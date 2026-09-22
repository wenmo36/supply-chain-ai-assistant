"""Run the approved end-to-end natural-language regression cases.

This command intentionally uses the real Agent -> MySQL -> renderer ->
Power BI artifact chain.  It is separate from pytest so it can be run from a
Windows PowerShell session without relying on pytest being installed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


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
from integrations.powerbi_adapter import write_powerbi_payload
from integrations.powerbi_report_builder import build_ai_page_from_payload
from visualization.renderer import LATEST_OUTPUT_PATH, render


@dataclass(frozen=True)
class RegressionCase:
    name: str
    question: str
    expected_chart_type: str
    validate: Callable[[object], None]


def _assert_metric(result, metric: str) -> None:
    if result.analysis_plan.get("metric") != metric:
        raise AssertionError(
            f"主指标应为 {metric}，实际为 {result.analysis_plan.get('metric')}"
        )


def _assert_ranking(result) -> None:
    _assert_metric(result, "purchase_amount")
    if result.analysis_plan.get("dimension") != "supplier":
        raise AssertionError("排名维度应为 supplier")
    if len(result.rows) > 5:
        raise AssertionError(f"TOP5 返回了 {len(result.rows)} 行")
    values = [float(row["purchase_amount"]) for row in result.rows]
    if values != sorted(values, reverse=True):
        raise AssertionError("采购金额排名未按降序排列")


def _assert_trend(result) -> None:
    _assert_metric(result, "purchase_amount")
    if result.analysis_plan.get("intent") != "trend":
        raise AssertionError("趋势问题的 intent 应为 trend")
    if result.analysis_plan.get("time_granularity") != "day":
        raise AssertionError("未指定粒度的趋势应默认为 day")
    if not result.rows or not all("period" in row for row in result.rows):
        raise AssertionError("趋势结果必须包含 period")


def _assert_over_receipt_orders(result) -> None:
    _assert_metric(result, "over_receipt_qty")
    if result.analysis_plan.get("dimension") != "order":
        raise AssertionError("超收明细维度应为 order")
    if not result.rows:
        raise AssertionError("超收明细不应为空")
    if not all(float(row["over_receipt_qty"]) > 0 for row in result.rows):
        raise AssertionError("超收明细包含非正数")


def _assert_unreceived_ranking(result) -> None:
    _assert_metric(result, "unreceived_qty")
    if result.analysis_plan.get("dimension") != "material":
        raise AssertionError("未收数量排名维度应为 material")
    if not result.rows:
        raise AssertionError("未收数量排名不应为空")
    values = [float(row["unreceived_qty"]) for row in result.rows]
    if not all(value > 0 for value in values):
        raise AssertionError("未收数量排名包含 0 值")
    if values != sorted(values, reverse=True):
        raise AssertionError("未收数量排名未按降序排列")


def _assert_summary(result) -> None:
    _assert_metric(result, "purchase_amount")
    if result.analysis_plan.get("intent") != "summary":
        raise AssertionError("月度汇总的 intent 应为 summary")
    if result.analysis_plan.get("dimension") is not None:
        raise AssertionError("纯汇总不应包含 dimension")
    if len(result.rows) != 1:
        raise AssertionError(f"月度汇总应返回 1 行，实际为 {len(result.rows)} 行")


def _assert_multi_metric(result) -> None:
    expected = {
        "purchase_amount",
        "receipt_rate",
        "unreceived_qty",
        "over_receipt_qty",
    }
    if set(result.analysis_plan.get("metrics") or []) != expected:
        raise AssertionError("多指标列表不完整")
    if not result.rows:
        raise AssertionError("多指标供应商对比不应为空")
    for row in result.rows:
        missing = expected.difference(row)
        if missing:
            raise AssertionError(f"供应商结果缺少指标列：{sorted(missing)}")


CASES = (
    RegressionCase(
        name="供应商采购金额 TOP5",
        question="采购金额最高的5个供应商",
        expected_chart_type="bar_chart",
        validate=_assert_ranking,
    ),
    RegressionCase(
        name="采购金额日趋势",
        question="按日查看采购金额趋势",
        expected_chart_type="line_chart",
        validate=_assert_trend,
    ),
    RegressionCase(
        name="订单超收明细",
        question="查询存在超收的采购订单",
        expected_chart_type="table",
        validate=_assert_over_receipt_orders,
    ),
    RegressionCase(
        name="物料未收数量 TOP5",
        question="未收数量最高的5种物料",
        expected_chart_type="bar_chart",
        validate=_assert_unreceived_ranking,
    ),
    RegressionCase(
        name="采购金额月度汇总",
        question="查询2026年8月采购金额",
        expected_chart_type="card",
        validate=_assert_summary,
    ),
    RegressionCase(
        name="供应商四指标对比",
        question="按供应商比较采购金额、收货率、未收数量和超收数量",
        expected_chart_type="multi_metric",
        validate=_assert_multi_metric,
    ),
)


def _check_artifacts(result, expected_chart_type: str, require_powerbi: bool) -> None:
    chart_type = result.chart_plan.get("chart_type")
    if chart_type != expected_chart_type:
        raise AssertionError(
            f"图表类型应为 {expected_chart_type}，实际为 {chart_type}"
        )

    chart_path = render(result)
    if not chart_path.exists():
        raise AssertionError(f"PNG 未生成：{chart_path}")
    if not LATEST_OUTPUT_PATH.exists():
        raise AssertionError(f"固定 PNG 未生成：{LATEST_OUTPUT_PATH}")

    if require_powerbi and not POWERBI_RESULT_PATH:
        raise AssertionError("--require-powerbi 要求设置 POWERBI_RESULT_PATH")
    if require_powerbi and not POWERBI_AUTO_BUILD:
        raise AssertionError("--require-powerbi 要求 POWERBI_AUTO_BUILD=true")

    if POWERBI_RESULT_PATH:
        json_path = write_powerbi_payload(result, POWERBI_RESULT_PATH)
        if not json_path.exists():
            raise AssertionError(f"Power BI JSON 未生成：{json_path}")

    if POWERBI_AUTO_BUILD:
        page_path = build_ai_page_from_payload(result, POWERBI_REPORT_ROOT)
        primary_visual = page_path / "visuals" / "f0a1b2c3d4e6" / "visual.json"
        secondary_visual = page_path / "visuals" / "f0a1b2c3d4e7" / "visual.json"
        if not primary_visual.exists() or not secondary_visual.exists():
            raise AssertionError("Power BI AI 页面视觉对象未完整生成")
        primary_document = json.loads(primary_visual.read_text(encoding="utf-8"))
        json.loads(secondary_visual.read_text(encoding="utf-8"))
        expected_visual_type = {
            "bar_chart": "barChart",
            "line_chart": "lineChart",
            "table": "pivotTable",
            "card": "card",
            "multi_metric": "barChart",
        }[expected_chart_type]
        actual_visual_type = primary_document["visual"]["visualType"]
        if actual_visual_type != expected_visual_type:
            raise AssertionError(
                f"Power BI 主视觉应为 {expected_visual_type}，"
                f"实际为 {actual_visual_type}"
            )


def run_regression_tests(*, require_powerbi: bool = False) -> int:
    configure_logging()
    logger = logging.getLogger(__name__)
    failures = 0

    print(f"开始运行 {len(CASES)} 个端到端回归用例\n")
    for index, case in enumerate(CASES, start=1):
        try:
            result = run_analysis(case.question)
            case.validate(result)
            _check_artifacts(result, case.expected_chart_type, require_powerbi)
            print(
                f"✅ [{index}/{len(CASES)}] {case.name} | "
                f"rows={len(result.rows)} | "
                f"chart={result.chart_plan.get('chart_type')} | "
                f"repairs={result.repair_count}"
            )
        except Exception as error:
            failures += 1
            logger.exception("Regression case failed: %s", case.name)
            print(f"❌ [{index}/{len(CASES)}] {case.name} | {error}")

    passed = len(CASES) - failures
    print(f"\n回归测试结果：{passed}/{len(CASES)} 通过")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="运行供应链 AI 端到端回归测试")
    parser.add_argument(
        "--require-powerbi",
        action="store_true",
        help="要求同时写入 Power BI JSON 并更新 PBIR AI 页面",
    )
    args = parser.parse_args()
    return run_regression_tests(require_powerbi=args.require_powerbi)


if __name__ == "__main__":
    raise SystemExit(main())
