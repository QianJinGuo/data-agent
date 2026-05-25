# 运维手册

## 环境要求

- Python 3.11+
- Node.js 18+
- npm 9+ 或 yarn
- Git

## 快速启动

### 方式一：后端 + 前端独立运行

**后端**

```bash
cd /Users/jinguo/PycharmProjects/data-agent
make install          # 安装 Python 依赖
make run-api         # 启动 FastAPI 服务 (http://localhost:8000)
```

**前端**

```bash
cd frontend
npm install          # 安装前端依赖
npm run dev          # 启动开发服务器 (http://localhost:5173)
```

### 方式二：Docker 部署

```bash
cd /Users/jinguo/PycharmProjects/data-agent
make docker-up       # 构建并启动后端 + 前端容器
```

访问：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式三：API 独立运行（无前端）

```bash
cd /Users/jinguo/PycharmProjects/data-agent
source .venv/bin/activate
uvicorn nl2sql.api:app --host 0.0.0.0 --port 8000 --reload
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-not-set`（Mock 模式）|
| `LLM_PROVIDER` | LLM 提供商 | `openai` |
| `LLM_MODEL` | LLM 模型名 | `gpt-4o` |

### 支持的 LLM 提供商

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export OPENAI_API_KEY=sk-ant-...
export LLM_PROVIDER=anthropic
export LLM_MODEL=claude-3-5-sonnet-6

# Local (Ollama)
export OPENAI_API_KEY=not-needed
export LLM_PROVIDER=local
export LLM_MODEL=llama3
```

### 数据库配置

后端默认使用 Mock 数据。如需连接真实数据库，修改 `src/nl2sql/db_connector.py`：

```python
from nl2sql.db_connectors import ClickHouseConnector

connector = ClickHouseConnector(
    host="localhost",
    port=9000,
    database="sales",
    username="default",
    password="",
)
```

## 测试

```bash
# 后端测试
make test

# 前端测试
cd frontend && npm run test
```

## API 使用示例

### NL2SQL 查询

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me sales by region"}'
```

### 创建营销活动

```bash
curl -X POST http://localhost:8000/marketing/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "High-value customer reactivation",
    "audience_description": "Customers who purchased in last 30 days",
    "channels": ["sms", "email"]
  }'
```

### 应用营销方案

```bash
curl -X POST http://localhost:8000/marketing/plans/{plan_id}/apply \
  -H "Content-Type: application/json" \
  -d '{"channels": ["sms"], "content": {"timing": "immediate"}}'
```

### 查看触达任务

```bash
curl http://localhost:8000/marketing/tasks
```

### 健康检查

```bash
curl http://localhost:8000/health
```

## 目录结构

```
data-agent/
├── src/nl2sql/           # Python 后端源码
│   ├── graph.py           # NL2SQL pipeline
│   ├── marketing_graph.py # Marketing pipeline
│   ├── orchestrator.py    # 编排器
│   ├── api.py             # FastAPI
│   └── ...                # 其他模块
├── frontend/              # React 前端
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── components/    # UI 组件
│   │   ├── api/           # API 客户端
│   │   └── types/         # TypeScript 类型
│   ├── dist/              # 构建产物
│   └── node_modules/      # 依赖
├── examples/              # 示例脚本
│   ├── run_query.py       # NL2SQL 查询示例
│   ├── run_marketing.py   # 营销策略示例
│   ├── run_orchestrator.py # 编排器示例
│   └── run_api.py         # API 服务示例
├── tests/                 # 测试
├── docs/                  # 文档
├── Makefile               # 构建命令
├── docker-compose.yml     # Docker 编排
├── Dockerfile.backend     # 后端镜像
├── Dockerfile.frontend    # 前端镜像
└── pyproject.toml         # Python 配置
```

## 常见问题

### Q: 前端无法连接后端

确认后端运行在 `http://localhost:8000`，前端 API client 指向正确地址。

### Q: Mock 模式和真实 LLM 模式的区别

- `OPENAI_API_KEY` 未设置或为 `sk-not-set` → Mock 模式，返回预设响应
- `OPENAI_API_KEY` 正确设置 → 真实 LLM，调用 OpenAI API

### Q: 如何添加新的数据库连接器

1. 在 `src/nl2sql/db_connector.py` 中继承 `DBConnector` 抽象类
2. 实现 `execute()` 方法
3. 在 `src/nl2sql/nodes.py` 的 `sql_execute` 节点中注册

### Q: 如何扩展 Chart 类型

修改 `src/nl2sql/chart_recommender.py` 中的 `CHART_KEYWORDS` 和推荐逻辑。

## 日志

后端日志输出到 stdout，Docker 模式下：

```bash
docker compose logs -f backend
```

## 构建生产版本

```bash
# 前端构建
cd frontend && npm run build
# 输出: frontend/dist/

# Python 包
make dist
```