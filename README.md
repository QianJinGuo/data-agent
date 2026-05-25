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

## Tech Stack

| Component | Technology |
|-----------|------------|
| Graph Framework | LangGraph 0.4+ |
| LLM | LangChain OpenAI (configurable: OpenAI / Anthropic / Local) |
| State | TypedDict + LangGraph StateGraph |
| Structured Output | JSON parsing from LLM responses |
| Chart Recommendation | Rule-based keyword + data shape heuristics |

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
│   ├── nodes.py        # 5 graph nodes
│   ├── graph.py       # build_graph() → compiled StateGraph
│   ├── chart_recommender.py
│   └── llm.py         # LLM wrapper (openai/anthropic/local)
├── examples/
│   └── run_query.py
├── tests/
│   └── test_pipeline.py
├── pyproject.toml
└── README.md
```