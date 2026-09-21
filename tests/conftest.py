"""Pytest configuration for unit and integration test separation."""

import os

import pytest


INTEGRATION_TEST_FILES = {
    "test_agent.py",
    "test_api.py",
    "test_grain_risk.py",
    "test_models.py",
    "test_mysql.py",
}


def _integration_enabled() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS") == "1"


if not _integration_enabled():
    # Allow modules that construct clients during import to be collected
    # without requiring real credentials for the default unit-test run.
    os.environ.setdefault("AI_API_KEY", "test-key")
    os.environ.setdefault("MYSQL_USER", "test-user")
    os.environ.setdefault("MYSQL_PASSWORD", "test-password")
    os.environ.setdefault("MYSQL_DATABASE", "test-database")


def pytest_collection_modifyitems(items):
    if _integration_enabled():
        return

    skip_integration = pytest.mark.skip(
        reason=(
            "需要 AI API 和/或 MySQL；"
            "设置 RUN_INTEGRATION_TESTS=1 后运行"
        )
    )

    for item in items:
        if item.path.name in INTEGRATION_TEST_FILES:
            item.add_marker(skip_integration)
