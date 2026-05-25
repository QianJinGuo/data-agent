# NL2SQL Data Agent — LangGraph Implementation

## Architecture

```
User Question
     │
     ▼
┌─────────────────────┐
│  intent_classify    │  LLM Structured Output → intent ∈ {query, compare, trend, attribution, other}
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  sql_generate       │  LLM + Few-shot + Schema Constraint → SQL query
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  sql_execute        │  Execute SQL against data source (mocked in MVP)
│  (conditional)      │  Error → go to interpret directly
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  attribution        │  Root cause analysis (decomposition + correlation)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  interpret          │  LLM → Natural language summary + chart recommendation
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  detect_anomaly     │  Statistical anomaly detection (z-score / IQR)
└─────────────────────┘
```

## Nodes

| Node | Input | Output | Description |
|------|-------|--------|-------------|
| `intent_classify` | messages, schema | intent | Classify user intent |
| `sql_generate` | messages, intent, schema | sql | Generate SQL from NL |
| `sql_execute` | sql | query_result or error | Execute SQL (mocked) |
| `attribution` | query_result | attribution_result | Root cause analysis |
| `interpret` | query_result, attribution | final_answer, chart_type | Natural language summary |
| `detect_anomaly` | query_result | anomaly_result | Statistical anomaly detection |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Graph Framework | LangGraph 0.4+ |
| LLM | LangChain OpenAI (configurable: OpenAI / Anthropic / Local) |
| State | TypedDict + LangGraph StateGraph |
| Structured Output | JSON parsing from LLM responses |
| Chart Recommendation | Rule-based keyword + data shape heuristics |
| Anomaly Detection | Statistical z-score and IQR methods |
| Multi-dataset Support | Cross-dataset query detection and schema merging |

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Example 1: Query by region

```python
from nl2sql.graph import build_graph
from nl2sql.schema import get_sample_dataset
from nl2sql.llm import build_llm
from langchain_core.messages import HumanMessage

llm = build_llm(provider="openai", model="gpt-4o", api_key="sk-...")
dataset = get_sample_dataset()
graph = build_graph(dataset, llm=llm)

result = graph.invoke({
    "messages": [HumanMessage(content="What are the sales by region?")],
    "intent": "", "sql": "", "query_result": None,
    "attribution_result": None, "chart_type": "table",
    "final_answer": "", "error": None,
})
print(result["final_answer"])
print(result["chart_type"])
```

### Example 2: CLI usage

```bash
export OPENAI_API_KEY=sk-...
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4o
python examples/run_query.py "Show me the monthly sales trend"
```

### Example 3: Time-series analysis

```python
result = graph.invoke({
    "messages": [HumanMessage(content="Show me the monthly trend of order count")],
    "intent": "", "sql": "", "query_result": None,
    "attribution_result": None, "chart_type": "table",
    "final_answer": "", "error": None,
})
print(result["final_answer"])
print(result["chart_type"])  # line
```

## Configuration

### LLM Providers

```python
# OpenAI (default)
llm = build_llm(provider="openai", model="gpt-4o", api_key="sk-...")

# Anthropic
llm = build_llm(provider="anthropic", model="claude-3-5-sonnet-6", api_key="sk-ant-...")

# Local (Ollama)
llm = build_llm(provider="local", model="llama3", base_url="http://localhost:11434")
```

### Custom Dataset

```python
from nl2sql.schema import Dataset, SemanticModel, Metric, Dimension

dataset = Dataset(
    id="ds_custom",
    name="My Dataset",
    tables=["my_table"],
    semantic_model=SemanticModel(
        metrics=[Metric(name="Revenue", expr="SUM(amount)", description="Total revenue")],
        dimensions=[Dimension(name="City", field="my_table.city")],
    ),
)
```

## Run Tests

```bash
pytest tests/
```

## Project Structure

```
data-agent/
├── src/nl2sql/
│   ├── __init__.py
│   ├── schema.py       # Dataset, SemanticModel, Metric, Dimension
│   ├── state.py        # AgentState TypedDict
│   ├── nodes.py        # 6 graph nodes
│   ├── graph.py        # build_graph() → compiled StateGraph
│   ├── chart_recommender.py
│   ├── llm.py          # LLM wrapper (openai/anthropic/local)
│   ├── anomaly.py      # Anomaly detection (z-score / IQR)
│   ├── conversation.py # Conversation manager with thread tracking
│   ├── multi_dataset.py # Multi-dataset manager with cross-dataset queries
│   └── scheduler.py    # Scheduled queries with cron expressions
├── examples/
│   └── run_query.py
├── tests/
│   └── test_pipeline.py
├── pyproject.toml
└── README.md
```

---

## Phase 2: Enhanced Capabilities

### Multi-dataset Support

The `MultiDatasetManager` class enables queries across multiple datasets:

```python
from nl2sql.multi_dataset import MultiDatasetManager

manager = MultiDatasetManager()
manager.add_dataset(dataset1)
manager.add_dataset(dataset2)

# Detect cross-dataset queries automatically
cross_ds_ids = manager.cross_dataset_query("Compare revenue and marketing spend")
```

Features:
- Cross-dataset query detection via LLM analysis
- Schema merging for queries spanning multiple datasets
- Dataset-level isolation with shared metadata

### Real Database Execution

SQLAlchemy-based connectors for production deployments:

```python
from nl2sql.db_connectors import ClickHouseConnector, MySQLConnector, DorisConnector

connector = ClickHouseConnector(host="localhost", database="sales")
result = connector.execute("SELECT region, SUM(amount) FROM orders GROUP BY region")
```

Features:
- Connection pooling for high throughput
- Graceful fallback to mock data when real DB is unavailable
- Support for ClickHouse, MySQL, and Doris

### Anomaly Detection

Statistical anomaly detection with automatic method selection:

```python
from nl2sql.anomaly import detect_anomaly

result = detect_anomaly(query_result, sensitivity=1.5, method="auto")
# Returns: is_anomaly, score, anomalies list, summary
```

Methods:
- **z-score**: For normally distributed data
- **IQR**: For skewed distributions
- **auto**: Automatically selects best method based on data characteristics

### Conversation Memory

`ConversationManager` tracks conversation history per thread:

```python
from nl2sql.conversation import ConversationManager

manager = ConversationManager()
manager.add_message(thread_id="thread-1", role="user", content="Show sales")
manager.add_message(thread_id="thread-1", role="assistant", content="Here are the sales...")

history = manager.get_history(thread_id="thread-1")
```

Features:
- Thread-based conversation tracking
- LLM summarization when context grows beyond threshold
- Cross-thread isolation

### Scheduled Push

`ScheduledQuery` with cron expressions for automated reporting:

```python
from nl2sql.scheduler import ScheduledQuery, Scheduler

query = ScheduledQuery(
    id="weekly-sales",
    cron_expr="0 9 * * MON",  # Every Monday at 9 AM
    query="Show weekly sales summary",
    recipients=["team@example.com"],
)

scheduler = Scheduler()
scheduler.add_query(query)
scheduler.run_forever()
```

Features:
- Cron expression parsing for flexible scheduling
- Email and recipient notification support
- Background scheduler loop with due query detection

### Enhanced Interpret Node

The interpret node now includes anomaly context in Chinese summary generation:

```python
result = graph.invoke({
    "messages": [HumanMessage(content="Show regional sales")],
    "intent": "", "sql": "", "query_result": None,
    "attribution_result": None, "chart_type": "table",
    "final_answer": "", "error": None,
    "conversation_id": "conv-1",
    "datasets": [],
    "anomaly_result": None,
})
# result["final_answer"] includes anomaly explanation in Chinese
# result["anomaly_result"] contains detection results
```

## Phase 2 Tech Stack Additions

| Component | Technology |
|-----------|------------|
| Database Connectors | SQLAlchemy (ClickHouse, MySQL, Doris) |
| Connection Pooling | SQLAlchemy pool management |
| Anomaly Detection | Statistical z-score + IQR |
| Conversation Memory | Thread-based history with LLM summarization |
| Scheduled Tasks | Cron expression parsing + background scheduler |
| Multi-dataset | Cross-dataset query detection + schema merging |