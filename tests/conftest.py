"""Safe opt-in controls for tests that use external services."""

import os

import pytest
from dotenv import load_dotenv


load_dotenv()

# Permit collection of application modules in the default offline test run.
os.environ.setdefault("AI_API_KEY", "test-key")
os.environ.setdefault("MYSQL_USER", "test-user")
os.environ.setdefault("MYSQL_PASSWORD", "test-password")
os.environ.setdefault("MYSQL_DATABASE", "test-database")


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        help="run tests that access the configured MySQL database",
    )
    parser.addoption(
        "--run-paid",
        action="store_true",
        help="run tests that spend configured AI API credits",
    )


def pytest_collection_modifyitems(config, items):
    run_integration = config.getoption("--run-integration")
    run_paid = config.getoption("--run-paid")

    skip_integration = pytest.mark.skip(
        reason="需要 MySQL；使用 --run-integration 显式启用"
    )
    skip_paid = pytest.mark.skip(
        reason="会消耗 AI API 点数；使用 --run-paid 显式启用"
    )
    skip_e2e = pytest.mark.skip(
        reason=(
            "需要 MySQL 且会消耗 AI API 点数；"
            "同时使用 --run-integration --run-paid 启用"
        )
    )

    for item in items:
        if "e2e" in item.keywords:
            if not (run_integration and run_paid):
                item.add_marker(skip_e2e)
        elif "paid_api" in item.keywords:
            if not run_paid:
                item.add_marker(skip_paid)
        elif "integration" in item.keywords:
            if not run_integration:
                item.add_marker(skip_integration)
