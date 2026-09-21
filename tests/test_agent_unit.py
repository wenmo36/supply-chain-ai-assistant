"""V2 Agent orchestration tests without external services."""

from ai import agent
from ai.analysis_result import AnalysisResult
from mysql.connector import ProgrammingError


def test_run_analysis_builds_standard_result(monkeypatch):
    plan = {
        "intent": "ranking",
        "metric": "purchase_amount",
        "dimension": "supplier",
    }
    chart_plan = {
        "chart_type": "bar_chart",
        "title": "供应商采购金额",
        "x_axis": "supplier",
        "y_axis": "purchase_amount",
        "sort": "desc",
        "orientation": "horizontal",
        "show_data_labels": True,
    }

    monkeypatch.setattr(agent, "parse_intent", lambda question: plan)
    monkeypatch.setattr(
        agent,
        "generate_sql",
        lambda analysis_plan: "SELECT 1 AS purchase_amount",
    )
    monkeypatch.setattr(
        agent,
        "validate_business_sql",
        lambda sql, analysis_plan: None,
    )
    monkeypatch.setattr(
        agent,
        "run_readonly_sql",
        lambda sql: [{"supplier_name": "测试供应商", "purchase_amount": 1}],
    )
    monkeypatch.setattr(agent, "build_chart_plan", lambda analysis_plan: chart_plan)

    result = agent.run_analysis("查询采购金额最高的供应商")

    assert isinstance(result, AnalysisResult)
    assert result.analysis_plan == plan
    assert result.chart_plan == chart_plan
    assert result.repair_count == 0


def test_run_analysis_repairs_invalid_sql_once(monkeypatch):
    plan = {"metric": "purchase_amount"}
    validations = []

    monkeypatch.setattr(agent, "parse_intent", lambda question: plan)
    monkeypatch.setattr(agent, "generate_sql", lambda analysis_plan: "SELECT bad")

    def validate(sql, analysis_plan):
        validations.append(sql)
        if sql == "SELECT bad":
            raise ValueError("指标公式错误")

    monkeypatch.setattr(agent, "validate_business_sql", validate)
    monkeypatch.setattr(
        agent,
        "repair_sql",
        lambda **kwargs: {
            "sql": "SELECT purchase_qty * unit_price FROM purchase_detail",
            "repair_reason": "修复指标公式",
        },
    )
    monkeypatch.setattr(agent, "run_readonly_sql", lambda sql: [])
    monkeypatch.setattr(
        agent,
        "build_chart_plan",
        lambda analysis_plan: {
            "chart_type": "table",
            "title": "测试",
            "x_axis": None,
            "y_axis": None,
            "sort": None,
            "orientation": None,
            "show_data_labels": False,
        },
    )

    result = agent.run_analysis("测试自动修复")

    assert result.repair_count == 1
    assert validations == [
        "SELECT bad",
        "SELECT purchase_qty * unit_price FROM purchase_detail",
    ]


def test_run_analysis_repairs_database_syntax_error(monkeypatch):
    plan = {"metric": "over_receipt_qty", "intent": "filter"}
    executed = []

    monkeypatch.setattr(agent, "parse_intent", lambda question: plan)
    monkeypatch.setattr(
        agent,
        "generate_sql",
        lambda analysis_plan: "SELECT order_no AS order FROM purchase_detail",
    )

    def validate(sql, analysis_plan):
        if " AS order " in f" {sql} ":
            raise ValueError("MySQL 保留字别名")

    monkeypatch.setattr(agent, "validate_business_sql", validate)
    monkeypatch.setattr(
        agent,
        "repair_sql",
        lambda **kwargs: {
            "sql": "SELECT order_no FROM purchase_detail",
            "repair_reason": "删除保留字别名",
        },
    )

    def execute(sql):
        executed.append(sql)
        return [{"order_no": "CG001"}]

    monkeypatch.setattr(agent, "run_readonly_sql", execute)
    monkeypatch.setattr(
        agent,
        "build_chart_plan",
        lambda analysis_plan: {
            "chart_type": "table",
            "title": "超收数量明细",
            "x_axis": None,
            "y_axis": None,
            "sort": None,
            "orientation": None,
            "show_data_labels": False,
        },
    )

    result = agent.run_analysis("哪些采购订单存在超收？")

    assert result.repair_count == 1
    assert executed == ["SELECT order_no FROM purchase_detail"]


def test_run_analysis_repairs_mysql_execution_error(monkeypatch):
    plan = {"metric": "purchase_amount", "intent": "summary"}
    attempts = []

    monkeypatch.setattr(agent, "parse_intent", lambda question: plan)
    monkeypatch.setattr(agent, "generate_sql", lambda analysis_plan: "SELECT broken")
    monkeypatch.setattr(
        agent,
        "validate_business_sql",
        lambda sql, analysis_plan: None,
    )

    def execute(sql):
        attempts.append(sql)
        if sql == "SELECT broken":
            raise ProgrammingError(msg="SQL syntax error", errno=1064)
        return [{"purchase_amount": 100}]

    monkeypatch.setattr(agent, "run_readonly_sql", execute)
    monkeypatch.setattr(
        agent,
        "repair_sql",
        lambda **kwargs: {
            "sql": "SELECT 100 AS purchase_amount",
            "repair_reason": "修复数据库语法错误",
        },
    )
    monkeypatch.setattr(
        agent,
        "build_chart_plan",
        lambda analysis_plan: {
            "chart_type": "card",
            "title": "采购金额",
            "x_axis": None,
            "y_axis": "purchase_amount",
            "sort": None,
            "orientation": None,
            "show_data_labels": True,
        },
    )

    result = agent.run_analysis("采购金额是多少？")

    assert result.repair_count == 1
    assert attempts == ["SELECT broken", "SELECT 100 AS purchase_amount"]
