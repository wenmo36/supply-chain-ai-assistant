"""
1:N JOIN 粒度风险测试

验证：
1. purchase_detail -> receipt_detail 是 1:N
2. 直接 JOIN 后 SUM(purchase_qty) 会产生重复风险
3. 风险检查器能够在执行前拦截
"""

import pytest

from database.schema import get_relationships
from tools.sql_risk_checker import validate_business_sql


pytestmark = pytest.mark.integration


def test_receipt_detail_is_n_to_one():
    """
    验证数据库存在：
    receipt_detail N : 1 purchase_detail
    """

    relationships = get_relationships()

    matched = [
        item
        for item in relationships
        if item["child_table"] == "receipt_detail"
        and item["parent_table"] == "purchase_detail"
    ]

    assert len(matched) == 1
    assert matched[0]["relationship"] == "N:1"


def test_purchase_amount_join_receipt_is_blocked():
    """
    purchase_detail JOIN receipt_detail 后，
    直接聚合 purchase_detail 指标应被拦截。
    """

    plan = {
        "metric": "purchase_amount"
    }

    sql = """
    SELECT
        pd.order_no,
        SUM(pd.purchase_qty * pd.unit_price) AS purchase_amount
    FROM purchase_detail pd
    JOIN receipt_detail rd
        ON pd.purchase_detail_id = rd.purchase_detail_id
    GROUP BY pd.order_no
    """

    with pytest.raises(ValueError, match="1:N|聚合风险"):
        validate_business_sql(
            sql,
            plan
        )
