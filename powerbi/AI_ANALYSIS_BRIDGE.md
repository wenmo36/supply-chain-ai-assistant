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

如果希望同时自动更新 PBIP 中的 `AI分析` 页面，再增加：

```text
POWERBI_AUTO_BUILD=true
POWERBI_REPORT_ROOT=D:\AI\supply_chain_ai_v1\powerbi\SupplyChainAI.Report
```

运行前建议先关闭 Power BI Desktop；程序会把 AI 页面写入 PBIR 文件，随后重新打开
`SupplyChainAI.pbip` 即可看到新增或更新的 `AI分析` 页面。原有的总览、供应商分析和
异常分析页面不会被覆盖。

## 数据契约

文件包含 `schema_version`、`generated_at`、`question`、`analysis_plan`、
`chart_plan`、`rows`、`sql` 和 `repair_count`。结果中的日期、时间和 Decimal
会先转换成 JSON 可处理的类型；不会写入 API Key 或 MySQL 密码。

这一步是本地 PBIR 页面生成，不等同于 Power BI Desktop 中无需重开文件的实时对话控件。
当前页面中的图表绑定现有语义模型度量，并按 AI 返回的维度值添加筛选；后续可继续
扩展日期筛选、更多图表类型和页面布局。
