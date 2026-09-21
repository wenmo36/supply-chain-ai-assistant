"""Translate technical exceptions into safe, actionable user messages."""

from mysql.connector import Error as MySQLError
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)


def format_user_error(error: Exception) -> str:
    if isinstance(error, AuthenticationError):
        return "AI API 鉴权失败，请检查 .env 中的 API Key。"

    if isinstance(error, APITimeoutError):
        return "AI 服务响应超时，请稍后重试或调大 AI_TIMEOUT_SECONDS。"

    if isinstance(error, APIConnectionError):
        return "无法连接 AI 服务，请检查网络和 AI_BASE_URL。"

    if isinstance(error, RateLimitError):
        return "AI 服务请求过于频繁，请稍后重试。"

    if isinstance(error, APIStatusError):
        if error.status_code == 402:
            return "AI 服务点数不足，请在 API2D 补充点数后重试。"
        return f"AI 服务返回错误（HTTP {error.status_code}）。"

    if isinstance(error, MySQLError):
        return "MySQL 操作失败，请检查数据库服务、账号权限和 .env 配置。"

    if isinstance(error, (ValueError, TypeError)):
        return str(error)

    return "运行失败，详细信息已写入 logs/app.log。"
