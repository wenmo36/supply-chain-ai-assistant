# Python AI → Power BI 结果桥接

Python Agent 可以把最近一次成功分析写入一个 UTF-8 JSON 文件，作为
Power BI Power Query 或其他下游接口的稳定输入。该功能默认关闭，不会改变
现有命令行行为。

## 启用

在本地 `.env` 中增加一个路径，例如：

```text
POWERBI_RESULT_PATH=D:\AI\supply_chain_ai_v1\output\powerbi\latest_analysis.json
```

然后运行：

```powershell
python main.py
```

每次成功执行问题后，文件会以原子替换方式更新。父目录不存在时会自动创建。

## 数据契约

文件包含 `schema_version`、`generated_at`、`question`、`analysis_plan`、
`chart_plan`、`rows`、`sql` 和 `repair_count`。结果中的日期、时间和 Decimal
会先转换成 JSON 可处理的类型；不会写入 API Key 或 MySQL 密码。

这一步是可审计的结果交接，不等同于 Power BI Desktop 中的实时对话控件。
确认 JSON 稳定后，再把它接成 Power Query 表或本地 API，即可继续做报表内的
AI 分析页。
