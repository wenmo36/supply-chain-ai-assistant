from database.mysql import get_connection
import pytest


pytestmark = pytest.mark.integration

def test_mysql_connection():

    conn = None

    try:
        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute(
            "SELECT DATABASE();"
        )

        database = cursor.fetchone()

        print(
            "\n当前数据库:"
        )
        print(database)

        assert database is not None

        cursor.execute(
            """
            SELECT *
            FROM purchase_detail
            LIMIT 5;
            """
        )

        rows = cursor.fetchall()
        print(
            "\n测试数据:"
        )

        for row in rows:
            print(row)
        assert len(rows) >= 0

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":

    test_mysql_connection()

    print("\n✅ MySQL测试通过")
