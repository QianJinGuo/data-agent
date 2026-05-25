# 架构文档

## 系统概览

Data Agent 是一个基于 LangGraph 的企业级数据智能体平台，包含两个核心 pipeline：

- **NL2SQL Pipeline** — 将自然语言转换为 SQL 查询，返回数据可视化结果
- **Marketing Strategy Pipeline** — 端到端营销策略自动化（人群圈选→策略生成→触达任务配置）

```
User Question
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│              DataAgentOrchestrator                       │
│          route_question() → nl2sql / marketing          │
└──────────┬─────────────────────────────────┬──────────────┘
           │                                 │
  ┌────────▼──────────┐            ┌────────▼──────────────┐
  │   NL2SQL Graph     │            │   Marketing Graph     │
  │  6-node pipeline   │            │  5-node pipeline       │
  └───────────────────┘            └───────────────────────┘
           │                                 │
           └────────────┬────────────────────┘
                        ▼
               FastAPI REST API
                        │
          ┌─────────────┴─────────────┐
          │                           │
     /query                   /marketing/campaigns
     /marketing/plans/{id}/apply  /marketing/tasks
```

## NL2SQL Pipeline（6节点）

```
intent_classify → sql_generate → sql_execute → attribution → interpret → detect_anomaly
```

| 节点 | 输入 | 输出 | 技术实现 |
|------|------|------|----------|
| `intent_classify` | messages, schema | intent | LLM Structured Output → {query, compare, trend, attribution, other} |
| `sql_generate` | messages, intent, schema | sql | LLM + Few-shot + Schema Constraint |
| `sql_execute` | sql | query_result / error | SQLAlchemy（Mock/ClickHouse/MySQL/Doris）|
| `attribution` | query_result | attribution_result | 分解 + 相关性分析（Mock）|
| `interpret` | query_result, attribution, anomaly | final_answer, chart_type | LLM 生成自然语言 + chart_recommender |
| `detect_anomaly` | query_result | anomaly_result | z-score + IQR 统计方法 |

### 条件边

- SQL 执行成功 → 进入 attribution
- SQL 执行失败 → 跳过 attribution → interpret（携带 error 信息）

### 数据模型

```python
AgentState(TypedDict):
  messages: list[BaseMessage]
  intent: str
  sql: str
  query_result: dict | None
  attribution_result: dict | None
  chart_type: str  # table|line|column_parallel|pie|measure_card
  final_answer: str
  error: str | None
  conversation_id: str
  datasets: list[str]
  anomaly_result: dict | None
  detection_result: dict | None
```

## Marketing Strategy Pipeline（5节点）

```
parse_objective → audience_build → plan_generate → strategy_generate → task_config
```

| 节点 | 输入 | 输出 | 技术实现 |
|------|------|------|----------|
| `parse_objective` | messages | campaign_objective, audience_hints | LLM Structured Output |
| `audience_build` | audience_hints | target_audience, audience_insights | CDPClient.build_audience() |
| `plan_generate` | target_audience | proposed_plans (N plans) | LLM 生成，人群/渠道/内容三个维度 |
| `strategy_generate` | selected_plan | generated_strategy | timing_design, channel_priority, content_variants |
| `task_config` | strategy | outreach_tasks, final_answer | OutreachTask 配置 |

### 数据模型

```python
MarketingAgentState(TypedDict):
  messages: list[BaseMessage]
  campaign_objective: str
  target_audience: dict | None      # from CDP
  audience_insights: str | None
  proposed_plans: list[dict]
  selected_plan: dict | None
  generated_strategy: dict | None
  outreach_tasks: list[dict]
  final_answer: str
  error: str | None
```

## DataAgentOrchestrator

统一入口，负责：

1. **路由** — `route_question(question)` → `nl2sql` / `marketing` / `other`
2. **NL2SQL 执行** — `run_nl2sql(question, conversation_id, datasets)`
3. **营销策略执行** — `run_marketing(objective, audience_hints)`
4. **自动路由** — `run(question)` 根据问题类型自动选择 pipeline

## 技术栈

| 层级 | 技术 |
|------|------|
| Graph Framework | LangGraph 0.4+ |
| LLM Integration | LangChain OpenAI（可配置 OpenAI / Anthropic / Local）|
| State Management | TypedDict + LangGraph StateGraph |
| DB Connectors | SQLAlchemy（ClickHouse / MySQL / Doris）|
| REST API | FastAPI + Pydantic + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + TailwindCSS + Recharts |
| Anomaly Detection | Statistical z-score + IQR |
| Conversation Memory | Thread-based + LLM summarization |
| Scheduled Tasks | Cron expression parsing |
| Multi-dataset | Cross-dataset query detection + schema merging |
| CDP Integration | Abstract CDPClient + MockCDPClient |

## 数据库架构

```
Dataset (语义模型数据集)
├── id: str
├── name: str
├── tables: list[str]
└── semantic_model: SemanticModel
    ├── metrics: list[Metric]
    │   ├── name: str
    │   ├── expr: str
    │   └── description: str
    └── dimensions: list[Dimension]
        ├── name: str
        ├── field: str
        └── description: str
```

## 前端架构

```
src/
├── pages/
│   ├── NL2SQLPage.tsx       # 聊天式查询界面
│   ├── MarketingPage.tsx    # 5步营销策略构建器
│   └── CampaignDetail.tsx   # 营销活动详情
├── components/
│   ├── NavBar.tsx            # 顶部导航
│   ├── ChatInput.tsx         # 查询输入
│   ├── ConversationList.tsx  # 历史记录
│   ├── QueryResult.tsx       # SQL + 答案 + 图表
│   ├── ChartView.tsx         # Recharts 可视化（table/line/bar/pie）
│   ├── CampaignBuilder.tsx   # 5步向导
│   ├── AudiencePreview.tsx   # 人群预览
│   ├── PlanSelector.tsx      # 方案选择
│   ├── StrategyConfig.tsx   # 策略配置
│   └── TaskList.tsx          # 触达任务列表
├── api/client.ts            # Axios API 客户端
└── types/index.ts            # TypeScript 类型定义
```

## API 架构

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/query` | NL2SQL 查询 |
| POST | `/marketing/campaigns` | 创建营销活动 |
| POST | `/marketing/plans/{plan_id}/apply` | 应用方案生成策略 |
| GET | `/marketing/tasks` | 列出触达任务 |
| GET | `/health` | 健康检查 |

## 扩展性设计

1. **多数据集** — `MultiDatasetManager` 支持跨库查询，自动合并 schema
2. **LLM 可插拔** — `build_llm(provider, model)` 支持 OpenAI / Anthropic / Local（Ollama）
3. **DB 连接器可扩展** — 抽象 `DBConnector` 基类，可新增 PostgreSQL / BigQuery 等
4. **CDP 集成** — 抽象 `CDPClient`，`MockCDPClient` 用于开发，真实环境替换为业务 CDP
5. **Chart 类型可扩展** — `chart_recommender.py` 基于规则，可扩展为 ML-based 推荐