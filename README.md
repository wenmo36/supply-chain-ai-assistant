# Supply Chain AI Assistant

供应链 AI 数据分析助手 V2。系统将自然语言问题转换为结构化分析计划，生成并校验只读 MySQL SQL，执行查询后返回统一分析结果，并可输出本地 PNG 图表。

Power BI 项目文件仍保留在仓库中，但当前开发重点是 Python V2 主链路。

## 当前能力

- 自然语言意图识别与标准化 Analysis Plan
- 采购金额、采购数量、收料数量和超收数量语义指标
- 供应商、采购订单、物料和日期分析维度
- 基于真实数据库 Schema 的 SQL 生成
- SELECT/WITH 白名单与危险操作拦截
- 1:N JOIN 粒度风险检查
- SQL 校验失败后的有限自动修复
- 标准化 `AnalysisResult`
- 柱状图、条形图、折线图、表格和指标卡 PNG 渲染

## V2 主流程

```text
用户问题
  -> 意图识别
  -> Analysis Plan
  -> SQL 生成
  -> 安全与业务风险校验
  -> 必要时自动修复（最多 2 次）
  -> MySQL 只读查询
  -> AnalysisResult
  -> 图表规划与 PNG 渲染
```

## 项目结构

```text
ai/             V2 Agent、意图、SQL、修复、图表规划与结果模型
config/         环境变量与运行配置
database/       MySQL 连接、查询和 Schema/关系读取
semantic/       指标、维度、术语和业务规则
tools/          SQL 安全检查与粒度风险检查
visualization/  本地 PNG 渲染器
tests/          单元测试与外部集成测试
archive/        V1 历史代码
powerbi/        暂缓开发的 Power BI PBIP 项目
main.py         V2 命令行入口
schema.sql      示例数据库结构与测试数据
```

## 环境要求

- Python 3.10+
- MySQL 8.0+
- 支持 OpenAI Chat Completions 接口及 JSON Schema 输出的模型服务

## 安装

Windows PowerShell：

```powershell
git clone https://github.com/wenmo36/supply-chain-ai-assistant.git
cd supply-chain-ai-assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```env
AI_API_KEY=your_api_key
AI_BASE_URL=https://oa.api2d.net/v1
AI_MODEL=your_model

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=supply_chain_ai
```

`.env` 包含敏感凭据，已经被 `.gitignore` 排除，不要提交到 GitHub。

## 初始化数据库

使用 MySQL 客户端执行：

```powershell
mysql -u root -p < schema.sql
```

也可以在 Navicat 等工具中打开并运行 `schema.sql`。该脚本会重建示例表，因此不要在包含正式数据的数据库中直接执行。

主要表：

| 表 | 粒度 | 说明 |
|---|---|---|
| `supplier` | 供应商 | 供应商维度 |
| `purchase_detail` | 采购明细 | 采购数量、价格和累计收货量 |
| `receipt_detail` | 单次收货明细 | 与采购明细构成 N:1 关系 |

## 启动

```powershell
python main.py
```

示例问题：

```text
查询采购金额最高的5个供应商
哪些采购订单存在超收？
```

程序会输出 Analysis Plan、最终 SQL、查询结果、SQL 修复次数，以及生成图表的本地路径。

## 测试

默认运行不需要真实 API 或 MySQL 的单元测试：

```powershell
pytest -q
```

需要验证 AI API、MySQL 和完整 Agent 时，先正确配置 `.env`，再运行：

```powershell
$env:RUN_INTEGRATION_TESTS = "1"
pytest -q
```

结束后可清除临时开关：

```powershell
Remove-Item Env:RUN_INTEGRATION_TESTS
```

## 已知边界

- 当前模型调用基于 Chat Completions 接口的 `response_format=json_schema`，所选服务与模型必须支持该能力。
- 中文图表字体优先使用 Windows 的微软雅黑、黑体或宋体；其他操作系统未安装中文字体时会给出提示。
- V2 Schema 与关系校验依赖可访问的 MySQL 数据库元数据。
- Power BI 暂不作为当前阶段的交付范围。

## 安全原则

- 数据库执行入口只接受 `SELECT` 或 `WITH` 查询。
- 禁止 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等写操作。
- 公开仓库中不得提交 API Key、数据库密码或未脱敏业务数据。
- 数据库账号建议只授予目标库的只读权限。

## 当前开发方向

1. 提升 V2 主链路的错误处理与可观察性。
2. 扩展可离线执行的 Agent、SQL 和语义层单元测试。
3. 增加更多供应链指标与业务维度。
4. 在 Python 分析能力稳定后再继续 Power BI 集成。
