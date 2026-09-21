"""
供应链业务术语词典

负责把用户自然语言中的业务表达
映射到系统内部统一的标准名称。
"""


GLOSSARY = {

    # =========================
    # 采购金额
    # =========================

    "采购金额": "purchase_amount",
    "采购额": "purchase_amount",
    "采购花费": "purchase_amount",
    "采购费用": "purchase_amount",

    # =========================
    # 采购数量
    # =========================

    "采购数量": "purchase_qty",
    "采购量": "purchase_qty",

    # =========================
    # 收料数量
    # =========================

    "收料数量": "received_qty",
    "收货数量": "received_qty",
    "到货数量": "received_qty",

    # =========================
    # 超收
    # =========================

    "超收": "over_receipt_qty",
    "超收数量": "over_receipt_qty",
    "超收量": "over_receipt_qty",

    "采购订单数": "purchase_order_count",
    "订单数量": "purchase_order_count",
    "供应商数": "supplier_count",
    "供应商数量": "supplier_count",
    "物料种类数": "material_count",
    "物料数量": "material_count",
    "未收数量": "unreceived_qty",
    "未到货数量": "unreceived_qty",
    "欠交数量": "unreceived_qty",
    "收货率": "receipt_rate",
    "到货率": "receipt_rate",
    "加权采购单价": "weighted_unit_price",
    "加权平均单价": "weighted_unit_price",

    # =========================
    # 维度
    # =========================

    "供应商": "supplier",
    "供应商名称": "supplier",

    "采购订单": "order",
    "订单": "order",

    "物料": "material",
    "商品": "material",
    "物料编码": "material",
    "物料名称": "material",

    "采购日期": "order_date",
    "下单日期": "order_date",

    "入库日期": "warehouse_date",
    "采购入库日期": "warehouse_date"

}
