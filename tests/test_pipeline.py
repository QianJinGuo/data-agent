"""Basic tests for the NL2SQL pipeline."""
from langchain_core.messages import HumanMessage
from nl2sql.graph import build_graph
from nl2sql.schema import get_sample_dataset
from nl2sql.llm import build_llm


class MockLLM:
    """Simple mock LLM that returns predictable JSON."""

    def invoke(self, prompt: str):
        class Response:
            content = '{"intent": "query", "reasoning": "mocked"}' if "Classify" in prompt else '{"sql": "SELECT region, SUM(amount) FROM sales GROUP BY region", "explanation": "mocked"}'
        return Response()


def test_build_graph():
    """Test that graph builds without error."""
    dataset = get_sample_dataset()
    llm = MockLLM()
    graph = build_graph(dataset, llm=llm)
    assert graph is not None


def test_pipeline_state_shape():
    """Test pipeline produces all required state fields."""
    dataset = get_sample_dataset()
    llm = MockLLM()
    graph = build_graph(dataset, llm=llm)

    initial_state = {
        "messages": [HumanMessage(content="Show sales by region")],
        "intent": "",
        "sql": "",
        "query_result": None,
        "attribution_result": None,
        "chart_type": "table",
        "final_answer": "",
        "error": None,
    }
    result = graph.invoke(initial_state)
    assert "intent" in result
    assert "sql" in result
    assert "query_result" in result
    assert "chart_type" in result


def test_schema_text():
    """Test semantic model schema text generation."""
    ds = get_sample_dataset()
    text = ds.get_schema_text()
    assert "Sales Dataset" in text
    assert "Metrics" in text
    assert "Dimensions" in text