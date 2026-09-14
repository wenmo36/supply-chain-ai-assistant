import re



def validate_sql(sql:str)->None:


    cleaned=(
        sql.strip()
        .rstrip(";")
        .strip()
    )


    if not re.match(
        r"^(SELECT|WITH)\b",
        cleaned,
        re.IGNORECASE
    ):

        raise ValueError(
            "安全拦截：只允许 SELECT 或 WITH 查询"
        )


    forbidden=re.compile(
        r"\b("
        r"INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|"
        r"CREATE|REPLACE|GRANT|REVOKE|CALL|"
        r"LOAD\s+DATA|INTO\s+OUTFILE"
        r")\b",
        re.IGNORECASE
    )


    if forbidden.search(cleaned):

        raise ValueError(
            "安全拦截：检测到禁止操作"
        )