"""Graph nodes for the NL2SQL LangGraph pipeline."""
import json
from langchain_core.messages import HumanMessage, AIMessage
from nl2sql.schema import Dataset
from nl2sql.chart_recommender import recommend_chart
from nl2sql.multi_dataset import MultiDatasetManager
from nl2sql import anomaly


def intent_classify(state: dict, llm, dataset: Dataset) -> dict:
    """Classify user intent: query/compare/trend/attribution/other."""
    schema_text = dataset.get_schema_text()
    last_msg = state["messages"][-1].content if state["messages"] else ""

    prompt = f"""Classify the user's intent for this NL2SQL query.

Schema:
{schema_text}

User question: {last_msg}

Return a JSON object with:
- "intent": one of [query, compare, trend, attribution, other]
- "reasoning": brief explanation

query: simple data retrieval (e.g. "what is the sales of region north")
compare: comparison across dimensions (e.g. "which region performed better")
trend: time-series analysis (e.g. "how did sales evolve over months")
attribution: why did something happen (e.g. "why did sales drop")
other: none of the above

Return JSON only, no markdown."""
    response = llm.invoke(prompt)
    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"intent": "query", "reasoning": "parse error, default to query"}

    return {"intent": parsed.get("intent", "query")}


def sql_generate(state: dict, llm, dataset: Dataset, multi_dataset_manager: MultiDatasetManager = None) -> dict:
    """Generate SQL from question + intent + semantic model.
    
    Supports multi-dataset queries by detecting if the question spans
    multiple datasets and including schemas from all relevant datasets.
    """
    intent = state.get("intent", "query")
    last_msg = state["messages"][-1].content if state["messages"] else ""

    # Check if this is a cross-dataset query
    multi_dataset_ids = []
    if multi_dataset_manager and multi_dataset_manager.datasets:
        multi_dataset_ids = multi_dataset_manager.cross_dataset_query(last_msg)

    # Determine which schemas to include
    if len(multi_dataset_ids) > 1:
        # Cross-dataset query: merge all relevant schemas
        schema_texts = []
        for ds_id in multi_dataset_ids:
            ds = multi_dataset_manager.get_dataset(ds_id)
            if ds:
                schema_texts.append(ds.get_schema_text())
        schema_text = "\n\n---\n\n".join(schema_texts)
        is_cross_dataset = True
    elif multi_dataset_manager and multi_dataset_manager.datasets:
        # Single dataset but from manager: check if question matches other datasets
        single_ds_id = multi_dataset_manager.cross_dataset_query(last_msg)
        if single_ds_id:
            ds = multi_dataset_manager.get_dataset(single_ds_id[0])
            schema_text = ds.get_schema_text() if ds else dataset.get_schema_text()
        else:
            schema_text = dataset.get_schema_text()
        is_cross_dataset = False
    else:
        # Default single dataset
        schema_text = dataset.get_schema_text()
        is_cross_dataset = False

    examples = """Examples:
Q: "What is the sales amount by region?"
SQL: SELECT sales.region AS region, SUM(sales.amount) AS sales_amount FROM sales GROUP BY sales.region ORDER BY sales_amount DESC

Q: "Show me the monthly trend of order count"
SQL: SELECT sales.month AS month, COUNT(sales.order_id) AS order_count FROM sales GROUP BY sales.month ORDER BY sales.month

Q: "Compare sales between North and South regions"
SQL: SELECT sales.region AS region, SUM(sales.amount) AS total_sales FROM sales WHERE sales.region IN ('North', 'South') GROUP BY sales.region ORDER BY total_sales DESC
"""

    cross_dataset_instruction = ""
    if is_cross_dataset:
        cross_dataset_instruction = """
This is a CROSS-DATASET query involving multiple datasets.
When generating SQL for cross-dataset queries:
1. Use table aliases or fully-qualified table names (dataset_id.table_name)
2. If JOIN is needed, use explicit JOIN syntax with appropriate keys
3. Include all necessary tables from each dataset
"""

    prompt = f"""Generate SQL for the user's question.
Use the semantic model to map business terms to physical fields.
{cross_dataset_instruction}

Schema:
{schema_text}

Intent: {intent}
User question: {last_msg}

{examples}

Return a JSON object with:
- "sql": the SQL query string
- "explanation": brief explanation of the SQL
- "datasets_used": list of dataset IDs used (for cross-dataset queries)

Return JSON only, no markdown."""
    response = llm.invoke(prompt)
    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"sql": "-- parse error", "explanation": "failed to parse LLM response"}

    sql = parsed.get("sql", "-- error")
    
    # Store datasets used in state if cross-dataset
    if is_cross_dataset and "datasets" not in state:
        return {"sql": sql, "datasets": multi_dataset_ids}
    
    return {"sql": sql}


def sql_execute(state: dict, dataset: Dataset) -> dict:
    """Execute SQL and return mock results. In production, connect to real DB."""
    sql = state.get("sql", "")
    if not sql or sql.startswith("--"):
        return {"error": "No valid SQL to execute", "query_result": None}

    # Mock execution: generate synthetic data based on SQL keywords
    try:
        if "region" in sql.lower():
            data = {
                "columns": ["region", "sales_amount"],
                "rows": [
                    {"region": "North", "sales_amount": 12350000},
                    {"region": "South", "sales_amount": 9800000},
                    {"region": "East", "sales_amount": 8700000},
                    {"region": "West", "sales_amount": 7600000},
                ],
            }
        elif "month" in sql.lower():
            data = {
                "columns": ["month", "order_count"],
                "rows": [
                    {"month": "2026-01", "order_count": 4521},
                    {"month": "2026-02", "order_count": 3890},
                    {"month": "2026-03", "order_count": 5234},
                    {"month": "2026-04", "order_count": 6102},
                    {"month": "2026-05", "order_count": 5876},
                ],
            }
        elif "category" in sql.lower():
            data = {
                "columns": ["category", "total_sales"],
                "rows": [
                    {"category": "Electronics", "total_sales": 18500000},
                    {"category": "Clothing", "total_sales": 12300000},
                    {"category": "Food", "total_sales": 8700000},
                ],
            }
        else:
            data = {
                "columns": ["metric", "value"],
                "rows": [{"metric": "total_sales", "value": 38450000}],
            }

        return {"query_result": data, "error": None}
    except Exception as e:
        return {"error": str(e), "query_result": None}


def attribution(state: dict) -> dict:
    """Perform root cause analysis on query results (mocked)."""
    result = state.get("query_result")
    if not result:
        return {"attribution_result": None}

    # Mock attribution: decompose by available dimensions
    rows = result.get("rows", [])
    if len(rows) >= 2:
        sorted_rows = sorted(rows, key=lambda r: list(r.values())[-1], reverse=True)
        top = sorted_rows[0]
        bottom = sorted_rows[-1]
        diff = list(top.values())[-1] - list(bottom.values())[-1]
        contribution = round((diff / list(top.values())[-1]) * 100, 1) if list(top.values())[-1] else 0

        attr_result = {
            "top_driver": top,
            "bottom_driver": bottom,
            "gap": diff,
            "contribution_pct": contribution,
            "insight": f"{list(top.keys())[0]}='{top[list(top.keys())[0]]}' is the primary driver, accounting for {contribution}% more than the lowest performer.",
        }
        return {"attribution_result": attr_result}
    return {"attribution_result": {"insight": "Not enough data for attribution analysis."}}


def detect_anomaly(state: dict) -> dict:
    """Run anomaly detection on query results.
    
    Reads query_result from state, calls anomaly.detect_anomaly(),
    and stores the result back in state.
    """
    query_result = state.get("query_result")
    if not query_result:
        return {"anomaly_result": None}
    
    anomaly_result = anomaly.detect_anomaly(query_result)
    return {"anomaly_result": anomaly_result}


def interpret(state: dict, llm, dataset: Dataset) -> dict:
    """Generate natural language summary of results."""
    error = state.get("error")
    if error:
        return {
            "final_answer": f"Query encountered an error: {error}. Please rephrase your question or check the data schema.",
            "chart_type": "table",
        }

    result = state.get("query_result")
    attr = state.get("attribution_result")
    intent = state.get("intent", "query")

    if not result:
        return {"final_answer": "No data was returned for your query.", "chart_type": "table"}

    columns = result.get("columns", [])
    rows = result.get("rows", [])

    # Determine chart type
    chart = recommend_chart(
        query=state["messages"][-1].content if state["messages"] else "",
        num_rows=len(rows),
        has_time_dimension="month" in str(columns).lower(),
        has_geography_dimension="region" in str(columns).lower(),
    )

    # Run anomaly detection if result exists
    anomaly_result = anomaly.detect_anomaly(result) if result else None

    # LLM-based interpretation with anomaly context
    prompt = f"""You are a data analyst. Summarize the following query results in plain Chinese.

Intent: {intent}
Columns: {columns}
Rows: {rows}

Attribution analysis: {attr}

Anomaly detection result: {anomaly_result}

Provide a concise summary with:
1. Key finding (1-2 sentences)
2. Supporting numbers
3. Business implication (1 sentence)
4. If anomalies were detected, explain what they mean in the context of the data

Return a JSON object with:
- "summary": the natural language summary
- "chart_type": the recommended chart type (already computed: {chart})

Return JSON only."""
    response = llm.invoke(prompt)
    try:
        parsed = json.loads(response.content)
        return {
            "final_answer": parsed.get("summary", f"Query returned {len(rows)} rows with columns: {', '.join(columns)}"),
            "chart_type": chart,
            "anomaly_result": anomaly_result,
        }
    except Exception:
        return {
            "final_answer": f"Query returned {len(rows)} rows. Top value: {rows[0] if rows else 'N/A'}",
            "chart_type": chart,
            "anomaly_result": anomaly_result,
        }