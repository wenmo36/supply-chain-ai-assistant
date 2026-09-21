import json
import logging

from ai.agent import run_analysis
from config.logging_config import configure_logging
from errors import format_user_error
from visualization.renderer import render


def main():
    configure_logging()
    logger = logging.getLogger(__name__)
    print("==============================")
    print("供应链 AI 数据分析助手 V2")
    print("输入 exit 退出")
    print("==============================")

    while True:
        question = input("\n你：").strip()

        if question.lower() in [
            "exit",
            "quit",
            "退出"
        ]:
            break

        try:
            result = run_analysis(question)

            print("\n--- Analysis Plan ---")
            print(json.dumps(
                result.analysis_plan,
                ensure_ascii=False,
                indent=2
            ))

            print("\n--- SQL ---")
            print(result.sql)

            print("\n--- 查询结果 ---")
            print(json.dumps(
                result.to_dict()["rows"],
                ensure_ascii=False,
                indent=2
            ))

            print(f"\nSQL 修复次数：{result.repair_count}")

            if result.rows:
                chart_path = render(result)
                print(f"图表已生成：{chart_path.resolve()}")
            else:
                print("查询结果为空，未生成图表。")

        except Exception as e:
            logger.exception("Analysis failed")
            print("\n错误:", format_user_error(e))
            print("详细日志：logs/app.log")


if __name__ == "__main__":
    main()
