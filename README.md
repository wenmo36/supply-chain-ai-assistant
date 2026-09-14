# Supply Chain AI Assistant

基于大语言模型（LLM）的供应链数据分析助手。

通过自然语言方式查询企业供应链数据，实现：

- 业务问题理解
- AI自动生成SQL
- SQL安全校验
- 数据库查询
- 分析结果返回

用户无需编写SQL，只需要描述业务需求，即可获取数据分析结果。

当前版本：

```
V1.1
```

---

# 1. 项目背景

在企业数字化管理过程中，ERP系统积累了大量业务数据，例如：

- 采购数据
- 供应商数据
- 库存数据
- 订单数据

传统数据分析通常需要：

1. 熟悉数据库结构
2. 编写SQL语句
3. 理解业务流程

本项目尝试结合：

- 大语言模型（LLM）
- SQL Agent
- MySQL数据库
- 供应链业务规则

构建一个面向企业数据分析场景的智能助手。

例如：

用户输入：

```
哪些采购订单存在超收？
```

系统自动完成：

```
用户问题
    ↓
AI理解业务含义
    ↓
生成SQL
    ↓
SQL安全检查
    ↓
执行查询
    ↓
返回分析结果
```

---

# 2. 当前实现功能

## 2.1 自然语言查询供应链数据

支持通过自然语言提出业务问题。

示例：

```
查询供应商采购金额TOP5
```

系统自动生成对应SQL，并返回分析结果。

---

## 2.2 AI SQL Agent

当前支持：

- SELECT查询
- 多表JOIN
- GROUP BY聚合分析
- HAVING条件过滤


示例：

业务问题：

```
哪些采购订单存在超收？
```

自动生成：

```sql
SELECT
    order_no,
    SUM(purchase_qty) AS purchase_qty,
    SUM(received_qty) AS received_qty
FROM purchase_detail
GROUP BY order_no
HAVING SUM(received_qty) > SUM(purchase_qty);
```

---

## 2.3 SQL安全检查

为了避免AI生成危险SQL，项目加入SQL安全检查模块。

允许执行：

```sql
SELECT
WITH
```

禁止：

```sql
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
```

确保AI只能进行数据查询分析，不会修改数据库。

---

## 2.4 MySQL供应链数据分析

当前连接数据库：

```
supply_chain_ai
```

主要数据表：

| 表名 | 类型 | 说明 |
|---|---|---|
| supplier | 维度表 | 供应商信息 |
| purchase_detail | 事实表 | 采购业务明细 |

---

# 3. 系统架构


```
用户问题

    ↓

LLM模型

    ↓

Prompt业务理解

    ↓

SQL生成

    ↓

SQL安全检查

    ↓

MySQL供应链数据库

    ↓

分析结果返回
```

---

# 4. 技术栈


| 模块 | 技术 |
|---|---|
| 编程语言 | Python |
| AI模型调用 | OpenAI Compatible API |
| API服务 | API2D |
| 数据库 | MySQL 8.0 |
| 数据库连接 | mysql-connector-python |
| 配置管理 | python-dotenv |
| 开发环境 | VS Code |

---

# 5. 项目结构


```
supply_chain_ai_v1/

│
├── main.py                  # 程序入口
│
├── ai/                      # AI模块
│   ├── model.py             # AI模型调用
│   └── prompt.py            # Prompt管理
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
├── tests/                   # 测试模块
│
├── schema.sql               # 数据库初始化脚本
│
├── requirements.txt         # Python依赖
│
├── .env.example             # 环境变量模板
│
└── README.md                # 项目说明
```

---

# 6. 运行环境要求

## 软件要求

```
Python >= 3.10

MySQL >= 8.0

VS Code
```

---

# 7. 项目安装部署


## 7.1 获取项目代码

克隆项目：

```bash
git clone <https://github.com/wenmo36/supply-chain-ai-assistant.git>
```

进入项目目录：

```bash
cd supply-chain-ai-assistant
```

---

## 7.2 创建Python虚拟环境

Windows：

```powershell
python -m venv .venv
```

激活：

```powershell
.\.venv\Scripts\Activate
```

成功后：

```
(.venv)
```

表示虚拟环境启动成功。

---

## 7.3 安装依赖

```powershell
pip install -r requirements.txt
```

---

# 8. 环境变量配置


在项目根目录创建：

```
.env
```

参考：

```
.env.example
```

配置：

```env
# AI配置

AI_API_KEY=your_api_key

AI_BASE_URL=https://oa.api2d.net/v1

AI_MODEL=your_model


# MySQL配置

MYSQL_HOST=127.0.0.1

MYSQL_PORT=3306

MYSQL_USER=root

MYSQL_PASSWORD=your_password

MYSQL_DATABASE=supply_chain_ai
```

注意：

```
.env
```

包含敏感信息，不上传GitHub。

---

# 9. 数据库初始化


使用：

```
Navicat
```

执行：

```
schema.sql
```

初始化数据库。

创建：

```
supplier

purchase_detail
```

等测试数据表。

---

# 10. 启动项目


确保虚拟环境已激活：

```powershell
python main.py
```

启动成功：

```
==============================

Supply Chain AI Assistant V1.1

输入 exit 退出

==============================
```

---

# 11. 测试


安装pytest：

```powershell
pip install pytest
```

运行测试：

```powershell
pytest
```

测试内容包括：

- API调用测试
- 模型调用测试
- MySQL连接测试
- SQL安全检查测试

---

# 12. 后续规划


## V1.2

ERP业务知识库

计划加入：

- 采购流程规则
- 库存分析规则
- 供应商评价规则


## V1.3

供应链分析模块：

- 供应商绩效分析
- 采购价格趋势分析
- 库存风险分析


## V1.4

BI数据可视化：

- Power BI Dashboard
- 自动分析报告


## V2.0

本地AI模型部署：

- GPU推理
- 私有化部署
- 企业知识库RAG

---

# License

Private project for learning and development.