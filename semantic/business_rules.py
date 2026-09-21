"""
供应链业务规则层

用于约束 AI：
1. 数据粒度
2. 表之间的关系
3. 聚合方式
4. 一对多 JOIN 风险
5. 超收业务规则
"""


BUSINESS_RULES = {

    "purchase_detail_grain": {
        "name": "采购明细粒度",
        "rule": "purchase_detail 是当前采购事实数据的基础粒度",
        "description": "一条 purchase_detail 记录代表一条采购明细"
    },

    "order_multi_detail": {
        "name": "订单与采购明细关系",
        "rule": "一个采购订单可以包含多个采购明细",
        "relationship": "order_no 1:N purchase_detail"
    },

    "supplier_multi_order": {
        "name": "供应商与采购明细关系",
        "rule": "一个供应商可以对应多个采购明细",
        "relationship": "supplier 1:N purchase_detail"
    },

    "supplier_join": {
        "name": "供应商关联规则",
        "rule": "supplier 与 purchase_detail 通过 supplier_id 关联",
        "join_condition": "supplier.supplier_id = purchase_detail.supplier_id"
    },

    "purchase_amount_grain": {
        "name": "采购金额计算粒度",
        "rule": "采购金额必须在 purchase_detail 粒度计算",
        "formula": "purchase_qty * unit_price"
    },

    "purchase_qty_grain": {
        "name": "采购数量计算粒度",
        "rule": "采购数量来自 purchase_detail.purchase_qty",
        "formula": "purchase_qty"
    },

    "received_qty_grain": {
        "name": "收料数量计算粒度",
        "rule": "收料数量来自 purchase_detail.received_qty",
        "formula": "received_qty"
    },

    "one_to_many_join_risk": {
        "name": "一对多 JOIN 聚合风险",
        "rule": "存在 1:N JOIN 时，禁止直接聚合父表指标",
        "description": (
            "父表记录 JOIN 到多个子表记录后，"
            "父表指标可能被重复展开，"
            "导致 SUM 结果被放大"
        )
    },

    "aggregate_before_join": {
        "name": "先聚合后关联",
        "rule": "涉及多个事实粒度时，应先在各自事实粒度完成聚合，再进行 JOIN"
    },

    "over_receipt": {
        "name": "采购超收",
        "rule": "累计收料数量大于采购数量时视为超收",
        "condition": "received_qty > purchase_qty",
        "formula": "received_qty - purchase_qty"
    },

    "over_receipt_order": {
        "name": "订单层超收",
        "rule": "判断订单是否超收时，应先按照订单粒度进行聚合",
        "formula": "SUM(received_qty) > SUM(purchase_qty)"
    },

    "purchase_amount_not_received_amount": {
        "name": "采购金额定义",
        "rule": "采购金额使用采购数量计算，不使用收料数量替代",
        "formula": "purchase_qty * unit_price"
    },

    "unreceived_qty": {
        "name": "未收数量",
        "rule": "未收数量不能为负数，超收明细按 0 计算",
        "formula": "GREATEST(purchase_qty - received_qty, 0)"
    },

    "receipt_rate": {
        "name": "收货率",
        "rule": "收货率使用汇总后的收料数量除以采购数量，并防止除零",
        "formula": "SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) * 100"
    },

    "time_granularity": {
        "name": "时间粒度",
        "rule": (
            "日使用 DATE(date_field)，月使用 DATE_FORMAT(date_field, '%Y-%m')，"
            "季度使用 YEAR 和 QUARTER，年使用 YEAR(date_field)"
        )
    },

    "date_range": {
        "name": "日期范围",
        "rule": "date_from 和 date_to 必须作为闭区间作用于 Analysis Plan 指定的日期字段"
    }

}
