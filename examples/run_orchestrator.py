"""Example: orchestrate between NL2SQL and Marketing using the orchestrator."""
import os
from nl2sql.orchestrator import DataAgentOrchestrator
from nl2sql.llm import build_llm
from nl2sql.graph import build_graph
from nl2sql.marketing_graph import build_marketing_graph
from nl2sql.cdp_client import MockCDPClient
from nl2sql.schema import get_sample_dataset

api_key = os.getenv("OPENAI_API_KEY", "sk-not-set")


def auto_route(question: str):
    """Auto-detect question type and route to appropriate pipeline."""
    llm = build_llm(provider="openai", model="gpt-4o", api_key=api_key)
    cdp = MockCDPClient()
    dataset = get_sample_dataset()
    nl2sql_g = build_graph(dataset, llm=llm)
    marketing_g = build_marketing_graph(llm=llm, cdp_client=cdp)

    orchestrator = DataAgentOrchestrator(
        nl2sql_graph=nl2sql_g,
        marketing_graph=marketing_g,
        cdp_client=cdp,
    )

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}")

    # Route first to see which pipeline is selected
    route = orchestrator.route_question(question)
    print(f"\n[R] Detected type: {route}")

    # Run with auto-routing
    result = orchestrator.run(question)

    if result.get("intent") or result.get("type") == "nl2sql":
        print(f"\n[NL2SQL Result]")
        print(f"  SQL: {result.get('sql', 'N/A')}")
        print(f"  Answer: {result.get('final_answer', 'N/A')}")
        print(f"  Chart: {result.get('chart_type', 'table')}")
    else:
        print(f"\n[Marketing Result]")
        audience = result.get("target_audience", {})
        print(f"  Audience: {audience.get('name', 'N/A')} ({audience.get('estimated_count', 'N/A')} users)")
        print(f"  Plans: {len(result.get('proposed_plans', []))} proposed")
        print(f"  Answer: {result.get('final_answer', 'N/A')}")


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else "What are the sales by region?"

    auto_route(question)