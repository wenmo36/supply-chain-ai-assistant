from tools.sql_checker import validate_sql

def test_select_allowed():

    sql = """
    SELECT *
    FROM purchase_detail;
    """

    validate_sql(sql)

    print(
        "✅ SELECT允许执行"
    )

def test_with_allowed():
    sql = """
    WITH temp AS
    (
        SELECT *
        FROM purchase_detail
    )

    SELECT *
    FROM temp;
    """

    validate_sql(sql)

    print(
        "✅ WITH允许执行"
    )

def test_insert_blocked():
    sql = """
    INSERT INTO supplier
    VALUES
    (100,'测试');
    """

    try:
        validate_sql(sql)

    except ValueError:
        print(
            "✅ INSERT成功拦截"
        )
        return

    raise Exception(
        "❌ INSERT未被拦截"
    )

def test_drop_blocked():
    sql = """
    DROP TABLE supplier;
    """

    try:

        validate_sql(sql)

    except ValueError:
        print(
            "✅ DROP成功拦截"
        )
        return

    raise Exception(
        "❌ DROP未被拦截"
    )

if __name__ == "__main__":
    print(
        "====== SQL安全测试 ======"
    )

    test_select_allowed()
    test_with_allowed()
    test_insert_blocked()
    test_drop_blocked()

    print(
        "\n✅ SQL安全测试全部通过"
    )