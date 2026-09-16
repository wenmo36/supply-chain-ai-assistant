"""
MySQL 数据库结构读取模块

负责读取当前数据库中的：
- 表名
- 字段名
- 数据类型
- 是否允许 NULL
- 主键
"""

from database.mysql import get_connection


def get_schema() -> dict:
    """
    读取当前 MySQL 数据库的真实表结构。
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