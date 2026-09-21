import os
from dotenv import load_dotenv


load_dotenv()


AI_MODEL = os.getenv(
    "AI_MODEL",
    "gpt-4.1-mini"
)


AI_API_KEY = os.environ["AI_API_KEY"]


AI_BASE_URL = os.getenv(
    "AI_BASE_URL",
    "https://oa.api2d.net/v1"
)

AI_TIMEOUT_SECONDS = float(
    os.getenv(
        "AI_TIMEOUT_SECONDS",
        "60"
    )
)

AI_MAX_RETRIES = int(
    os.getenv(
        "AI_MAX_RETRIES",
        "1"
    )
)

AI_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "AI_MAX_OUTPUT_TOKENS",
        "1200"
    )
)


MYSQL_CONFIG = {

    "host": os.getenv(
        "MYSQL_HOST",
        "127.0.0.1"
    ),

    "port": int(
        os.getenv(
            "MYSQL_PORT",
            "3306"
        )
    ),

    "user": os.environ["MYSQL_USER"],

    "password": os.environ["MYSQL_PASSWORD"],

    "database": os.environ["MYSQL_DATABASE"]

}
