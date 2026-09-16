"""
MySQL 数据库元数据模块

负责读取：
1. 表
2. 字段
3. 数据类型
4. 主键
5. 外键
6. 表之间的关系
"""

from database.mysql import get_connection


def get_schema() -> dict:
    """
    读取当前数据库的表结构。
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_KEY
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
        )

        rows = cursor.fetchall()

        schema = {}

        for row in rows:
            table_name = row["TABLE_NAME"]

            if table_name not in schema:
                schema[table_name] = {
                    "columns": []
                }

            schema[table_name]["columns"].append({
                "name": row["COLUMN_NAME"],
                "data_type": row["DATA_TYPE"],
                "nullable": row["IS_NULLABLE"],
                "key": row["COLUMN_KEY"]
            })

        return schema

    finally:
        cursor.close()
        conn.close()


def get_relationships() -> list[dict]:
    """
    读取当前数据库中的外键关系。

    返回格式：

    [
        {
            "child_table": "purchase_detail",
            "child_column": "supplier_id",
            "parent_table": "supplier",
            "parent_column": "supplier_id",
            "relationship": "N:1"
        }
    ]
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                TABLE_NAME AS child_table,
                COLUMN_NAME AS child_column,
                REFERENCED_TABLE_NAME AS parent_table,
                REFERENCED_COLUMN_NAME AS parent_column
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY
                TABLE_NAME,
                ORDINAL_POSITION
            """
        )

        rows = cursor.fetchall()

        relationships = []

        for row in rows:
            relationships.append({
                "child_table": row["child_table"],
                "child_column": row["child_column"],
                "parent_table": row["parent_table"],
                "parent_column": row["parent_column"],
                "relationship": "N:1"
            })

        return relationships

    finally:
        cursor.close()
        conn.close()