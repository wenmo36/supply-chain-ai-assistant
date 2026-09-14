from typing import Any

from database.mysql import get_connection

from tools.sql_checker import validate_sql



def run_readonly_sql(
        sql:str
)->list[dict[str,Any]]:


    validate_sql(sql)


    conn=get_connection()

    cursor=conn.cursor(
        dictionary=True
    )


    try:

        cursor.execute(sql)

        rows=cursor.fetchall()


        return [
            dict(row)
            for row in rows
        ]


    finally:

        cursor.close()

        conn.close()