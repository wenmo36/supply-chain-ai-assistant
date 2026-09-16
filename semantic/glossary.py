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