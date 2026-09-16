"""
统一分析结果模块

负责把：
1. Analysis Plan
2. SQL
3. SQL 查询结果
4. Chart Plan

组合成统一的 Analysis Result。

后续 Power BI、本地可视化、报告生成器
都可以直接消费这个标准对象。
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class AnalysisResult:
    """
    标准化分析结果。
    """

    question: str
    analysis_plan: dict
    sql: str
    rows: list[dict[str, Any]]
    chart_plan: dict
    repair_count: int = 0

    def to_dict(self) -> dict:
        """
        转换成适合 JSON / API / Power BI Adapter
        使用的普通 dict。
        """

        return {
            "question": self.question,
            "analysis_plan": self.analysis_plan,
            "sql": self.sql,
            "rows": self._serialize_rows(),
            "chart_plan": self.chart_plan,
            "repair_count": self.repair_count
        }

    def _serialize_rows(self) -> list[dict]:
        """
        将 Decimal 等 MySQL 数据类型
        转换成 JSON 可处理的类型。
        """

        serialized = []

        for row in self.rows:

            new_row = {}

            for key, value in row.items():

                if isinstance(value, Decimal):
                    new_row[key] = float(value)

                else:
                    new_row[key] = value

            serialized.append(new_row)

        return serialized