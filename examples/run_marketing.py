"""Example: run a marketing campaign through the DataAgentOrchestrator."""
import os
from nl2sql.orchestrator import DataAgentOrchestrator
from nl2sql.llm import build_llm
from nl2sql.graph import build_graph
from nl2sql.marketing_graph import build_marketing_graph
from nl2sql.cdp_client import MockCDPClient
from nl2sql.schema import get_sample_dataset

api_key = os.getenv("OPENAI_API_KEY", "sk-not-set")


def run_marketing_campaign(objective: str, audience_hints: str):
    """Run a marketing campaign through the pipeline."""
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
    print(f"Marketing Campaign")
    print(f"Objective: {objective}")
    print(f"Audience hints: {audience_hints}")
    print(f"{'='*60}")

    result = orchestrator.run_marketing(objective, audience_hints)

    print(f"\n[Audience]")
    audience = result.get("target_audience", {})
    print(f"  ID: {audience.get('id', 'N/A')}")
    print(f"  Name: {audience.get('name', 'N/A')}")
    print(f"  Estimated count: {audience.get('estimated_count', 'N/A')}")
    print(f"  Insights: {audience.get('insights', 'N/A')}")

    print(f"\n[Proposed Plans]")
    for plan in result.get("proposed_plans", []):
        print(f"  - {plan.get('name', 'N/A')}: {plan.get('description', 'N/A')}")

    print(f"\n[Final Answer]")
    print(f"  {result.get('final_answer', 'N/A')}")

    return result


if __name__ == "__main__":
    import sys

    objective = sys.argv[1] if len(sys.argv) > 1 else "High-value customer reactivation campaign"
    audience_hints = sys.argv[2] if len(sys.argv) > 2 else "Customers who purchased in last 30 days, age 25-40, total spend > 1000"

    run_marketing_campaign(objective, audience_hints)