import json
import os
import re
from typing import Any

import mysql.connector
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("AI_MODEL", "gpt-4.1-mini")

client = OpenAI(
    api_key=os.environ["AI_API_KEY"],
    base_url="https://oa.api2d.net/v1",
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_readonly_sql",
            "description": (
                "在供应链 MySQL 数据库中执行只读 SQL 查询。"
                "只能执行 SELECT / WITH 查询，不允许 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等写操作。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的只读 MySQL SQL 查询。"
                    }
                },
                "required": ["sql"],
                "additionalProperties": False,
            },
        },
    }
]

SYSTEM_PROMPT = """
你是一名供应链数据分析师，也是 SQL 专家。

数据库中有两张表：

supplier(
    supplier_id INT,
    supplier_name VARCHAR(100)
)

purchase_detail(
    purchase_detail_id INT,
    order_no VARCHAR(30),
    order_date DATE,
    supplier_id INT,
    material_code VARCHAR(30),
    material_name VARCHAR(100),
    purchase_qty DECIMAL(18,2),
    unit_price DECIMAL(18,2),
    received_qty DECIMAL(18,2),
    warehouse_date DATE
)

重要业务规则：
1. purchase_detail 是采购明细粒度，一行代表一个采购订单中的一个物料明细。
2. 同一个 order_no 可以有多个明细行。
3. purchase_qty * unit_price 可以用于计算采购金额。
4. received_qty 可能与 purchase_qty 不相等，存在超收或少收。
5. supplier 是供应商维度表，supplier_id 是关联键。
6. 回答涉及“采购金额”时，优先在 purchase_detail 粒度聚合，避免不必要的 1:N JOIN。
7. 只能通过 run_readonly_sql 查询数据库，不允许修改数据库。
8. 查询完成后，要基于真实查询结果回答，不要编造数据。
9. 回答尽量解释 SQL 与业务含义，让学习者能理解。
"""

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
    )

def validate_sql(sql: str) -> None:
    cleaned = sql.strip().rstrip(";").strip()

    if not re.match(r"^(SELECT|WITH)\b", cleaned, re.IGNORECASE):
        raise ValueError("安全拦截：只允许 SELECT 或 WITH 查询。")

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|CALL|LOAD\s+DATA|INTO\s+OUTFILE)\b",
        re.IGNORECASE,
    )
    if forbidden.search(cleaned):
        raise ValueError("安全拦截：检测到禁止的写入或管理操作。")

def run_readonly_sql(sql: str) -> list[dict[str, Any]]:
    validate_sql(sql)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()

def ask(question: str) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    first = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0,
    )

    assistant = first.choices[0].message
    messages.append(assistant)

    if not assistant.tool_calls:
        print("\nAI：\n" + (assistant.content or "没有返回内容"))
        return

    for tool_call in assistant.tool_calls:
        if tool_call.function.name != "run_readonly_sql":
            continue

        args = json.loads(tool_call.function.arguments)
        sql = args["sql"]

        print("\n--- AI 生成的 SQL ---")
        print(sql)

        try:
            rows = run_readonly_sql(sql)
        except Exception as exc:
            tool_result = {"error": str(exc)}
        else:
            tool_result = {
                "row_count": len(rows),
                "rows": rows[:200],
            }

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, ensure_ascii=False, default=str),
            }
        )

    final = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
    )

    print("\n--- AI 分析结果 ---")
    print(final.choices[0].message.content or "没有返回内容")

def main():
    print("========================================")
    print("供应链 AI 数据分析助手 V1")
    print("输入 exit 退出")
    print("========================================")

    while True:
        question = input("\n你：").strip()

        if not question:
            continue

        if question.lower() in {"exit", "quit", "退出"}:
            break

        try:
            ask(question)
        except Exception as exc:
            print(f"\n程序错误：{exc}")

if __name__ == "__main__":
    main()
