"""Run an end-to-end NL2SQL query through the LangGraph pipeline."""
import os
from langchain_core.messages import HumanMessage
from nl2sql.graph import build_graph
from nl2sql.schema import get_sample_dataset
from nl2sql.llm import build_llm

# Use environment variable or default placeholder
api_key = os.getenv("OPENAI_API_KEY", "sk-not-set")


def run_query(question: str, provider: str = "openai", model: str = "gpt-4o"):
    """Run a single query through the pipeline and print results."""
    llm = build_llm(provider=provider, model=model, api_key=api_key)
    dataset = get_sample_dataset()
    graph = build_graph(dataset, llm=llm)

    initial_state = {
        "messages": [HumanMessage(content=question)],
        "intent": "",
        "sql": "",
        "query_result": None,
        "attribution_result": None,
        "chart_type": "table",
        "final_answer": "",
        "error": None,
    }

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"Model: {provider}/{model}")
    print(f"{'='*60}")

    result = graph.invoke(initial_state)

    print(f"\n[Intent Classification]")
    print(f"  Intent: {result.get('intent', 'N/A')}")

    print(f"\n[SQL Generation]")
    print(f"  SQL: {result.get('sql', 'N/A')}")

    qr = result.get("query_result")
    if qr:
        print(f"\n[Query Result]")
        print(f"  Columns: {qr.get('columns', [])}")
        for row in qr.get("rows", []):
            print(f"  - {row}")
    else:
        err = result.get("error", "Unknown error")
        print(f"\n[Error] {err}")

    attr = result.get("attribution_result")
    if attr:
        print(f"\n[Attribution Analysis]")
        print(f"  {attr.get('insight', 'N/A')}")

    print(f"\n[Final Answer]")
    print(f"  {result.get('final_answer', 'N/A')}")
    print(f"  Chart type: {result.get('chart_type', 'table')}")


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else "What are the sales by region?"

    # Allow specifying provider/model via env or args
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gpt-4o")

    run_query(question, provider=provider, model=model)  # type: ignore[arg-type]