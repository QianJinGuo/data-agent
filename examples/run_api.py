"""Example: run the FastAPI REST API server."""
import os
from nl2sql.api import create_app
from nl2sql.llm import build_llm
from nl2sql.graph import build_graph
from nl2sql.marketing_graph import build_marketing_graph
from nl2sql.cdp_client import MockCDPClient
from nl2sql.schema import get_sample_dataset

api_key = os.getenv("OPENAI_API_KEY", "sk-not-set")


def create_server():
    """Create and configure the FastAPI app with all dependencies."""
    llm = build_llm(provider="openai", model="gpt-4o", api_key=api_key)
    dataset = get_sample_dataset()
    nl2sql_g = build_graph(dataset, llm=llm)
    marketing_g = build_marketing_graph(llm=llm, cdp_client=MockCDPClient())

    from nl2sql.orchestrator import DataAgentOrchestrator
    cdp = MockCDPClient()
    orchestrator = DataAgentOrchestrator(
        nl2sql_graph=nl2sql_g,
        marketing_graph=marketing_g,
        cdp_client=cdp,
    )

    app = create_app(orchestrator=orchestrator)
    return app


if __name__ == "__main__":
    import uvicorn

    app = create_server()
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting Data Agent API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)