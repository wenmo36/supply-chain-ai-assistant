"""Build the generated AI page in a PBIP report from latest_analysis.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from integrations.powerbi_report_builder import build_ai_page_from_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 Power BI AI分析 页面")
    parser.add_argument(
        "--result-path",
        default="output/powerbi/latest_analysis.json",
        help="AI 结果 JSON 路径",
    )
    parser.add_argument(
        "--report-root",
        default="powerbi/SupplyChainAI.Report",
        help="SupplyChainAI.Report 目录",
    )
    args = parser.parse_args()
    payload = json.loads(Path(args.result_path).read_text(encoding="utf-8"))
    page_path = build_ai_page_from_payload(payload, args.report_root)
    print(f"AI 页面已生成：{page_path.resolve()}")


if __name__ == "__main__":
    main()
