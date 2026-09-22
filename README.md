# Supply Chain AI Data Analysis Assistant

供应链 AI 数据分析助手。项目将自然语言业务问题转换为结构化分析计划，生成并校验只读 MySQL SQL，执行查询后输出统一分析结果，并同步生成本地 PNG 图表、Power BI JSON 结果和 Power BI PBIP/PBIR 页面。

当前稳定版本：**v1.2.0**

- [v1.2.0 Release](https://github.com/wenmo36/supply-chain-ai-assistant/releases/tag/v1.2.0)
- [GitHub Repository](https://github.com/wenmo36/supply-chain-ai-assistant)

## 项目定位

用户不需要编写 SQL，只需用自然语言描述供应链问题，例如：

~~~text
按供应商比较采购金额、收货率、未收数量和超收数量
~~~

系统会完成：

~~~text
自然语言问题
  -> 意图识别与 Analysis Plan
  -> SQL 生成
  -> 只读、安全与业务粒度校验
  -> 必要时有限自动修复
  -> MySQL 查询
  -> AnalysisResult
  -> 图表规划与 PNG 渲染
  -> JSON 结果交接
  -> Power BI AI 页面更新
~~~

Power BI 集成采用本地 PBIP/PBIR 文件更新方式，不依赖 Power BI Service API 或登录云端工作区。

## v1.2.0 已实现

与 v1.1.0 的基础自然语言 SQL 查询相比，v1.2.0 已完成并验证：

- 自然语言到结构化分析计划、SQL、结果和图表的完整链路。
- 采购金额、采购数量、累计收料数量、收货率、未收数量、超收数量、订单数、供应商数、物料种类数和加权采购单价等指标。
- 按供应商、采购订单、物料、采购日期和入库日期分析。
- SELECT/WITH 白名单、危险操作拦截、真实 Schema/关系校验和 1:N JOIN 粒度风险检查。
- SQL 业务校验失败后的有限自动修复，最多尝试 2 次。
- 柱状图、条形图、折线图、表格、指标卡和多指标对比图表。
- 生成带明细表的 Power BI AI 分析页；多指标问题会同时生成主图和完整明细表。
- 将最近一次分析写入 UTF-8 JSON，并在开启配置后自动更新 PBIP 中的 AI分析 页面。
- 保留原有 Power BI 报表页面；生成器只创建或更新 AI分析 页面。
- 六个端到端回归用例全部通过，最近一次验证为 6/6 通过且 SQL 修复次数均为 0。

## 支持的指标与维度

### 指标

| 业务名称 | Analysis Plan key | 说明 |
|---|---|---|
| 采购金额 | purchase_amount | SUM(purchase_qty × unit_price) |
| 采购数量 | purchase_qty | 采购明细中的采购数量 |
| 累计收料数量 | received_qty | purchase_detail 中的累计收料数量 |
| 收货率 | receipt_rate | SUM(received_qty) / NULLIF(SUM(purchase_qty), 0) × 100 |
| 未收数量 | unreceived_qty | SUM(GREATEST(purchase_qty - received_qty, 0)) |
| 超收数量 | over_receipt_qty | 收料数量超过采购数量的部分 |
| 采购订单数 | purchase_order_count | COUNT(DISTINCT order_no) |
| 供应商数 | supplier_count | COUNT(DISTINCT supplier_id) |
| 物料种类数 | material_count | COUNT(DISTINCT material_code) |
| 加权采购单价 | weighted_unit_price | 采购金额 / 采购数量 |

CLI、JSON 和 PNG 中的收货率使用百分数数值表示，例如 100.35 表示 100.35%；Power BI 使用百分比格式显示相同含义。

### 维度

| 业务名称 | Analysis Plan key | 字段 |
|---|---|---|
| 供应商 | supplier | supplier.supplier_name |
| 采购订单 | order | purchase_detail.order_no |
| 物料 | material | purchase_detail.material_code / material_name |
| 采购日期 | order_date | purchase_detail.order_date |
| 入库日期 | warehouse_date | purchase_detail.warehouse_date |

超收判断会按具体分析粒度处理；查询“存在超收的采购订单”时，系统会先按 order_no 汇总采购数量和收料数量，再用 HAVING 判断超收，避免把单条明细判断误当成订单结论。

## Power BI 自动更新

仓库中包含可直接用 Power BI Desktop 打开的 PBIP 项目：

~~~text
powerbi/SupplyChainAI.pbip
~~~

需要在环境变量中开启：

~~~env
POWERBI_RESULT_PATH=output/powerbi/latest_analysis.json
POWERBI_AUTO_BUILD=true
POWERBI_REPORT_ROOT=powerbi/SupplyChainAI.Report
~~~

运行一次分析后：

1. 结果写入 POWERBI_RESULT_PATH 指定的 JSON。
2. PBIR 生成器更新 AI分析 页面及其视觉对象。
3. Power BI Desktop 检测到报表定义变化时，选择允许更新即可看到结果。

AI分析 页的主视觉会根据问题使用柱状图、折线图、表格、指标卡或多指标主图；第二个视觉用于明细表或辅助对象。已有的供应链总览、供应商分析和采购与收货异常页面不会被生成器删除。

Power BI 模型默认从 MySQL 的 supply_chain_ai 数据库导入数据。首次打开 PBIP 时，请先确认 MySQL 连接和凭据可用。

## 项目结构

~~~text
ai/             Agent、意图识别、SQL 生成/修复、结果模型、图表规划
config/         环境变量、日志和运行配置
database/       MySQL 连接、查询、Schema 与关系读取
semantic/       指标、维度、术语和业务规则
integrations/   Power BI JSON 交接与 PBIR 页面生成
tools/          SQL 安全检查、粒度风险检查、一次性分析和回归 runner
visualization/  PNG 图表渲染器
tests/          离线单元测试与可选外部集成测试
powerbi/        PBIP、Report 和 SemanticModel 定义
archive/        V1 历史代码
main.py         交互式命令行入口
schema.sql      示例数据库结构与测试数据
requirements.txt
.env.example
~~~

## 环境要求

- Python 3.10+
- MySQL 8.0+
- 支持 OpenAI Chat Completions 接口和 response_format=json_schema 的模型服务
- 如需自动更新报表，需要 Power BI Desktop

## 安装

Windows PowerShell：

~~~powershell
git clone https://github.com/wenmo36/supply-chain-ai-assistant.git
cd supply-chain-ai-assistant

python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt

Copy-Item .env.example .env
~~~

如需复现已发布版本：

~~~powershell
git checkout v1.2.0
~~~

## 环境变量

在项目根目录编辑 .env：

~~~env
AI_API_KEY=your_api_key
AI_BASE_URL=https://oa.api2d.net/v1
AI_MODEL=your_model
AI_TIMEOUT_SECONDS=60
AI_MAX_RETRIES=1
AI_MAX_OUTPUT_TOKENS=1200

# 仅使用 Python/PNG 时可以留空
POWERBI_RESULT_PATH=output/powerbi/latest_analysis.json
POWERBI_AUTO_BUILD=true
POWERBI_REPORT_ROOT=powerbi/SupplyChainAI.Report

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=supply_chain_ai
~~~

说明：

- AI_API_KEY、MYSQL_USER、MYSQL_PASSWORD 和 MYSQL_DATABASE 是必需配置。
- POWERBI_RESULT_PATH 为空时，不写 Power BI JSON。
- POWERBI_AUTO_BUILD=false 时，不修改 PBIR 页面。
- 相对路径以项目根目录为基准，也可以改为绝对路径。
- .env 含有 API Key 和数据库密码，已被 .gitignore 排除，禁止提交到 GitHub。

## 初始化数据库

schema.sql 用于创建 supply_chain_ai 示例数据库和测试数据：

~~~powershell
mysql -u root -p < schema.sql
~~~

也可以在 Navicat 等 MySQL 客户端中执行该脚本。

主要数据表：

| 表 | 数据粒度 | 说明 |
|---|---|---|
| supplier | 供应商 | 供应商维度 |
| purchase_detail | 采购明细 | 订单、物料、采购数量、单价和累计收料数量 |
| receipt_detail | 单次收货明细 | 与采购明细构成一对多关系 |

注意：schema.sql 会删除并重建示例表。请只在开发或测试数据库执行；正式数据库应先备份并使用迁移脚本。采购金额、采购数量等 purchase_detail 指标不要直接与 receipt_detail 做未聚合的一对多 JOIN，否则可能重复计算。

## 运行分析

### 交互式模式

~~~powershell
python main.py
~~~

输入自然语言问题，输入 exit、quit 或 退出结束会话。

### 一次性模式

适合 PowerShell、脚本和自动化测试：

~~~powershell
python tools/run_analysis_once.py "按供应商比较采购金额、收货率、未收数量和超收数量"
~~~

程序会输出：

- Analysis Plan
- 最终 SQL
- 查询结果
- SQL 修复次数
- 命名 PNG 路径
- output/latest_analysis.png 固定副本
- 开启 Power BI 配置时的 JSON 和 AI 页面路径

可尝试的问题：

~~~text
采购金额最高的5个供应商
按日查看采购金额趋势
查询存在超收的采购订单
未收数量最高的5种物料
查询2026年8月采购金额
按供应商比较采购金额、收货率、未收数量和超收数量
~~~

## 测试

### 离线单元测试

默认不连接 MySQL，也不会消耗 AI API 点数：

~~~powershell
pytest -q
~~~

### 按需启用外部测试

~~~powershell
# 访问配置的 MySQL
pytest -q --run-integration

# 消耗配置的 AI API 点数
pytest -q --run-paid

# 同时访问 MySQL 并调用 AI API
pytest -q --run-integration --run-paid
~~~

### 已批准的端到端回归测试

该 runner 使用真实的 Agent -> MySQL -> PNG -> Power BI 文件链路，共 6 个用例。需要配置 MySQL、AI 服务，并在需要验证 Power BI 时打开两个开关：

~~~powershell
python tools/run_regression_tests.py --require-powerbi
~~~

验证项目包括：

| 用例 | 期望结果 |
|---|---|
| 供应商采购金额 TOP5 | bar_chart |
| 采购金额日趋势 | line_chart |
| 订单超收明细 | table |
| 物料未收数量 TOP5 | bar_chart |
| 采购金额月度汇总 | card |
| 供应商四指标对比 | multi_metric |

成功标准为：

~~~text
回归测试结果：6/6 通过
~~~

批量运行回归测试时，Power BI Desktop 可能对每次 PBIR 文件变化弹出更新提示；可以关闭 Desktop 后运行，或按提示允许更新。

## 输出文件

默认输出目录为 output/，该目录已加入 .gitignore：

~~~text
output/
  latest_analysis.png
  powerbi/
    latest_analysis.json
  <问题标题>.png
~~~

PBIP 报表定义位于 powerbi/SupplyChainAI.Report/definition/，其中 AI分析 页面由生成器维护并且可以提交到 Git。运行分析产生的 PNG、JSON、日志和临时文件不应提交。

## 故障排查

| 现象 | 检查项 |
|---|---|
| 提示缺少 AI_API_KEY 或 MySQL 配置 | 确认根目录存在 .env，并检查变量名是否与 .env.example 完全一致 |
| MySQL 连接失败 | 检查服务、端口、用户名、密码、数据库名，并确认已执行 schema.sql |
| Power BI 没有新页面或内容 | 确认 POWERBI_RESULT_PATH、POWERBI_AUTO_BUILD=true、POWERBI_REPORT_ROOT 正确，并打开的是 powerbi/SupplyChainAI.pbip |
| Power BI 提示报表已更改 | 选择允许更新；批量回归时可先关闭 Desktop |
| 查询有结果但没有 PNG | 检查 rows 是否为空，以及 output 目录是否可写 |
| 中文图表字体出现警告 | Windows 优先使用微软雅黑、黑体或宋体；其他系统需自行安装中文字体 |
| 收货率超过 100% | 这表示累计收料数量超过采购数量；同时查看超收数量列，而不是把该值当成错误 |

## 安全与边界

- 数据库执行入口只接受 SELECT 或 WITH 查询。
- INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等写操作会被拦截。
- SQL 业务规则会检查事实表粒度、日期字段、聚合方式和一对多 JOIN 风险。
- AI 自动修复有次数上限，连续不通过时会拒绝执行 SQL。
- 模型服务必须支持结构化 JSON Schema 输出。
- Power BI 自动更新是本地文件集成，不等同于 Power BI Service 发布。
- 不要把 API Key、数据库密码、未脱敏业务数据或正式库直接放进仓库。

## 后续方向

v1.2.0 已完成自然语言分析、PNG 输出、Power BI AI 页面和端到端回归验证。后续可以在不改变只读安全边界的前提下继续扩展：

1. 更多供应链指标、筛选条件和业务维度。
2. 更丰富的 Power BI 视觉对象和交互式筛选。
3. Web 对话入口、权限控制和定时分析。
4. 更完整的 CI 回归与部署文档。

## License

Private project for learning and development.
