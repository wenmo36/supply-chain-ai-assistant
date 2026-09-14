# 供应链 AI 数据分析助手 V1.1

基于 **LLM + Python + MySQL** 构建的供应链智能数据分析助手。

用户可以通过自然语言提出供应链分析问题，例如：

- 哪些采购订单存在超收？
- 供应商采购金额 TOP5 是哪些？
- 某采购订单包含哪些物料？
- 采购订单和入库数据关联统计有什么风险？

系统通过大语言模型生成 SQL 查询，并调用 MySQL 数据库获取真实业务数据，最后由 AI 根据查询结果进行业务分析。


---

# 一、项目功能

## 当前已实现功能

✅ 自然语言查询供应链数据
例如：
哪些采购订单存在超收？
系统自动生成：
```sql
SELECT ...
FROM purchase_detail
GROUP BY order_no
HAVING ...
并返回分析结果。

✅ AI 自动生成 SQL
支持：
SELECT 查询
多表 JOIN
GROUP BY 聚合
HAVING 条件分析

✅ MySQL 数据分析
连接供应链数据库：
supply_chain_ai
当前主要数据表：
supplier
供应商维度表
purchase_detail
采购明细事实表

✅ SQL 安全检查
限制 AI 只能执行：
SELECT
WITH
禁止：
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
避免 AI 误修改数据库。

二、技术栈
模块	技术
编程语言	Python
AI模型调用	OpenAI Compatible API
API中转	    API2D
数据库	    MySQL
数据库连接	mysql-connector-python
配置管理	python-dotenv
开发环境	VS Code

三、项目结构
supply_chain_ai_v1/
│
├── main.py                  # 程序入口
│
├── ai/                      # AI相关模块
│   ├── model.py             # AI模型调用
│   └── prompt.py            # ERP业务提示词
│
├── database/                # 数据库模块
│   ├── mysql.py             # MySQL连接
│   └── query.py             # SQL执行
│
├── tools/                   # 工具模块
│   └── sql_checker.py       # SQL安全检查
│
├── config/                  # 配置模块
│   └── settings.py          # 环境配置读取
│
├── schema.sql               # 数据库初始化脚本
│
├── requirements.txt         # Python依赖
│
├── .env                     # 本地配置文件
│
└── README.md                # 项目说明

四、运行环境要求
软件要求
Python >= 3.10
MySQL >= 8.0
VS Code（推荐）

五、项目启动步骤
1. 进入项目目录
Windows PowerShell：
cd D:\AI\supply_chain_ai_v1
确认当前目录：
pwd
应该显示：
D:\AI\supply_chain_ai_v1
2. 创建虚拟环境（首次运行）
如果还没有虚拟环境：
python -m venv .venv
3. 激活虚拟环境
Windows PowerShell：
.\.venv\Scripts\Activate
成功后终端显示：
(.venv) PS D:\AI\supply_chain_ai_v1>
表示已经进入Python虚拟环境。

六、配置环境变量
项目根目录创建：
.env

内容示例：
# AI配置
AI_API_KEY=你的API密钥
AI_BASE_URL=https://oa.api2d.net/v1
AI_MODEL=你的模型名称

# MySQL配置

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DATABASE=supply_chain_ai

注意：
.env 不上传到公开仓库。
可以参考：
.env.example
创建自己的配置文件。

七、数据库初始化
如果第一次运行，需要初始化数据库。
打开：
Navicat

创建查询。
执行：
schema.sql

该脚本会创建：
supplier
purchase_detail
等测试数据表。

八、启动程序
确保虚拟环境已激活：
python main.py

成功启动：
==============================
供应链 AI 数据分析助手 V1.1
输入 exit 退出
==============================

tips:
    -m 是让 Python 以模块(module)方式运行代码，而不是把它当成一个普通文件运行。

    通过安装pytest:pip install pytest
    运行:pytest
    pytest
    会自动：
    找项目根目录
    加载测试文件
    处理模块路径