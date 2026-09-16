"""
供应链指标语义层

这里定义业务指标的标准含义，
供后续 AI 意图识别、SQL 生成和业务规则校验使用。
"""


METRICS = {

    "purchase_amount": {
        "name": "采购金额",
        "description": "采购订单明细金额",
        "formula": "purchase_qty * unit_price",
        "fact_table": "purchase_detail",
        "grain": "purchase_detail",
        "aggregation": "SUM",
        "sql_expression": "purchase_qty * unit_price",
        "unit": "元",
        "risks": [
            "必须在 purchase_detail 粒度计算",
            "与一对多明细表直接 JOIN 后可能导致金额重复",
            "采购金额不能使用 received_qty 计算"
        ]
    },

    "purchase_qty": {
        "name": "采购数量",
        "description": "采购明细中向供应商下达的采购数量",
        "formula": "purchase_qty",
        "fact_table": "purchase_detail",
        "grain": "purchase_detail",
        "aggregation": "SUM",
        "sql_expression": "purchase_qty",
        "unit": "数量",
        "risks": [
            "purchase_detail 是采购数量的事实粒度",
            "与一对多明细表 JOIN 时可能重复计算"
        ]
    },

    "received_qty": {
        "name": "收料数量",
        "description": "供应商实际累计提供的数量",
        "formula": "received_qty",
        "fact_table": "purchase_detail",
        "grain": "purchase_detail",
        "aggregation": "SUM",
        "sql_expression": "received_qty",
        "unit": "数量",
        "risks": [
            "收料数量可能与采购数量不同",
            "可能出现超收"
        ]
    },

    "over_receipt_qty": {
        "name": "超收数量",
        "description": "实际累计收料数量超过采购数量的部分",
        "formula": "received_qty - purchase_qty",
        "fact_table": "purchase_detail",
        "grain": "purchase_detail",
        "aggregation": "SUM",
        "sql_expression": "received_qty - purchase_qty",
        "unit": "数量",
        "conditions": [
            "received_qty > purchase_qty"
        ],
        "risks": [
            "判断超收时需要根据具体分析粒度进行聚合",
            "订单层面的超收不能简单依赖单条明细判断"
        ]
    }

}