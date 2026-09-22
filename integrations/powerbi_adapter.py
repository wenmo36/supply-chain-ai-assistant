"""Stable JSON handoff from the Python agent to Power BI.

The adapter is deliberately file-based and opt-in.  It gives Power Query (or
another downstream consumer) a stable contract without coupling the agent to
Power BI Desktop or requiring an always-on web service.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ai.analysis_result import AnalysisResult


POWERBI_SCHEMA_VERSION = "1.0"


def build_powerbi_payload(result: AnalysisResult) -> dict:
    """Build a JSON-safe, versioned payload for Power BI ingestion."""

    serialized = result.to_dict()
    return {
        "schema_version": POWERBI_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question": serialized["question"],
        "analysis_plan": serialized["analysis_plan"],
        "chart_plan": serialized["chart_plan"],
        "rows": serialized["rows"],
        "sql": serialized["sql"],
        "repair_count": serialized["repair_count"],
    }


def write_powerbi_payload(result: AnalysisResult, path: str | Path) -> Path:
    """Atomically write *result* as UTF-8 JSON and return the target path."""

    target = Path(path).expanduser()
    if not str(path).strip():
        raise ValueError("Power BI 结果路径不能为空")

    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_powerbi_payload(result)
    temporary_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            prefix=f".{target.name}.",
            dir=target.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

    return target
