"""
供应链分析维度定义

维度用于回答：
“按什么来分析？”

例如：
- 按供应商
- 按采购订单
- 按物料
- 按日期
"""


DIMENSIONS = {

    "supplier": {
        "name": "供应商",
        "table": "supplier",
        "key": "supplier_id",
        "label": "supplier_name",
        "type": "entity"
    },

    "order": {
        "name": "采购订单",
        "table": "purchase_detail",
        "key": "order_no",
        "type": "entity"
    },

    "material": {
        "name": "物料",
        "table": "purchase_detail",
        "key": "material_code",
        "label": "material_name",
        "type": "entity"
    },

    "order_date": {
        "name": "采购日期",
        "table": "purchase_detail",
        "field": "order_date",
        "type": "date"
    },

    "warehouse_date": {
        "name": "入库日期",
        "table": "purchase_detail",
        "field": "warehouse_date",
        "type": "date"
    }

}