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
    },

    "purchase_order_count": {
        "name": "采购订单数",
        "description": "去重后的采购订单数量",
        "formula": "COUNT(DISTINCT order_no)",
        "fact_table": "purchase_detail",
        "grain": "purchase_order",
        "aggregation": "COUNT_DISTINCT",
        "sql_expression": "COUNT(DISTINCT order_no)",
        "unit": "单"
    },

    "supplier_count": {
        "name": "供应商数",
        "description": "发生采购业务的去重供应商数量",
        "formula": "COUNT(DISTINCT supplier_id)",
        "fact_table": "purchase_detail",
        "grain": "supplier",
        "aggregation": "COUNT_DISTINCT",
        "sql_expression": "COUNT(DISTINCT supplier_id)",
        "unit": "家"
    },

    "material_count": {
        "name": "物料种类数",
        "description": "发生采购业务的去重物料编码数量",
        "formula": "COUNT(DISTINCT material_code)",
        "fact_table": "purchase_detail",
        "grain": "material",
        "aggregation": "COUNT_DISTINCT",
        "sql_expression": "COUNT(DISTINCT material_code)",
        "unit": "种"
    },

    "unreceived_qty": {
        "name": "未收数量",
        "description": "采购数量扣除累计收料数量后的未收部分，不计负数",
        "formula": "GREATEST(purchase_qty - received_qty, 0)",
        "fact_table": "purchase_detail",
        "grain": "purchase_detail",
        "aggregation": "SUM",
        "sql_expression": "GREATEST(purchase_qty - received_qty, 0)",
        "unit": "数量",
        "risks": [
            "超收明细的未收数量必须按 0 计算",
            "与一对多明细表 JOIN 时可能重复计算"
        ]
    },

    "receipt_rate": {
        "name": "收货率",
        "description": "累计收料数量占采购数量的百分比",
        "formula": "SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) * 100",
        "fact_table": "purchase_detail",
        "grain": "analysis_group",
        "aggregation": "RATIO",
        "sql_expression": (
            "SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) * 100"
        ),
        "unit": "%"
    },

    "weighted_unit_price": {
        "name": "加权采购单价",
        "description": "采购金额除以采购数量得到的加权平均单价",
        "formula": (
            "SUM(purchase_qty * unit_price) "
            "/ NULLIF(SUM(purchase_qty), 0)"
        ),
        "fact_table": "purchase_detail",
        "grain": "analysis_group",
        "aggregation": "RATIO",
        "sql_expression": (
            "SUM(purchase_qty * unit_price) "
            "/ NULLIF(SUM(purchase_qty), 0)"
        ),
        "unit": "元/单位"
    }

}
