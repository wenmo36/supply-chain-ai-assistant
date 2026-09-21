from datetime import date, datetime

from ai.analysis_result import AnalysisResult


def test_dates_are_serialized_for_cli_json():
    result = AnalysisResult(
        question="测试",
        analysis_plan={},
        sql="SELECT 1",
        rows=[
            {
                "order_date": date(2026, 8, 1),
                "created_at": datetime(2026, 8, 1, 12, 30),
            }
        ],
        chart_plan={},
    )

    rows = result.to_dict()["rows"]

    assert rows[0]["order_date"] == "2026-08-01"
    assert rows[0]["created_at"] == "2026-08-01T12:30:00"
