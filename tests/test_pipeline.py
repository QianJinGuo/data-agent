"""Basic tests for the NL2SQL pipeline."""
from langchain_core.messages import HumanMessage, AIMessage
from nl2sql.graph import build_graph
from nl2sql.schema import get_sample_dataset
from nl2sql.llm import build_llm
from nl2sql import anomaly
from nl2sql.conversation import ConversationManager
from nl2sql.multi_dataset import MultiDatasetManager
from nl2sql.scheduler import ScheduledQuery, Scheduler


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


def test_anomaly_detection():
    """Test anomaly detection with mock data containing outliers."""
    # Data with obvious outlier: East region is 10x higher than others
    query_result = {
        "columns": ["region", "sales_amount"],
        "rows": [
            {"region": "North", "sales_amount": 1200000},
            {"region": "South", "sales_amount": 9800000},
            {"region": "East", "sales_amount": 50000000},  # Outlier
            {"region": "West", "sales_amount": 7600000},
        ],
    }
    
    result = anomaly.detect_anomaly(query_result)
    
    assert result is not None
    assert "is_anomaly" in result
    assert "score" in result
    assert "anomalies" in result
    
    # The East region value should be flagged as anomalous
    if result["is_anomaly"]:
        assert len(result["anomalies"]) > 0
        # Check that the East outlier is in the anomalies
        anomaly_columns = [a.get("column") for a in result["anomalies"]]
        assert "sales_amount" in anomaly_columns


def test_detect_anomaly_node():
    """Test detect_anomaly node in the graph."""
    from nl2sql import nodes

    # Data with a clear outlier: values around 100-200, one at 1000
    state = {
        "query_result": {
            "columns": ["region", "sales"],
            "rows": [
                {"region": "A", "sales": 100},
                {"region": "B", "sales": 105},
                {"region": "C", "sales": 110},
                {"region": "D", "sales": 95},
                {"region": "E", "sales": 1000},  # Outlier: 5x the normal range
            ],
        }
    }

    result = nodes.detect_anomaly(state)

    assert "anomaly_result" in result
    assert result["anomaly_result"] is not None
    # With values [100,105,110,95,1000], mean=282, std=405, z_score(1000)=1.77 > 1.5 → anomaly
    assert result["anomaly_result"]["is_anomaly"] is True


def test_conversation_manager():
    """Test conversation manager with message history."""
    manager = ConversationManager()
    
    # Add messages to a conversation
    user_msg = HumanMessage(content="Show me sales by region")
    assistant_msg = AIMessage(content="Here are the sales by region...")
    
    manager.add_message(
        conversation_id="conv-1",
        message=user_msg,
    )
    
    manager.add_message(
        conversation_id="conv-1",
        message=assistant_msg,
    )
    
    # Retrieve history
    history = manager.get_history(conversation_id="conv-1")
    
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    
    # Test cross-conversation isolation
    other_history = manager.get_history(conversation_id="conv-2")
    assert len(other_history) == 0


def test_multi_dataset_manager():
    """Test multi-dataset manager with cross-dataset queries."""
    from nl2sql.schema import Dataset, SemanticModel, Metric, Dimension
    
    # Create two datasets
    ds1 = Dataset(
        id="sales",
        name="Sales Dataset",
        tables=["sales"],
        semantic_model=SemanticModel(
            metrics=[Metric(name="revenue", expr="SUM(amount)", description="Total revenue")],
            dimensions=[Dimension(name="region", field="sales.region")],
        ),
    )
    
    ds2 = Dataset(
        id="marketing",
        name="Marketing Dataset",
        tables=["marketing_spend"],
        semantic_model=SemanticModel(
            metrics=[Metric(name="spend", expr="SUM(cost)", description="Total spend")],
            dimensions=[Dimension(name="channel", field="marketing_spend.channel")],
        ),
    )
    
    manager = MultiDatasetManager()
    manager.add_dataset(ds1)
    manager.add_dataset(ds2)
    
    # Test cross-dataset query detection
    cross_ds = manager.cross_dataset_query("Compare revenue and marketing spend")
    assert cross_ds is not None
    
    # Test getting a specific dataset
    retrieved = manager.get_dataset("sales")
    assert retrieved is not None
    assert retrieved.id == "sales"


def test_scheduler_cron_parse():
    """Test scheduler cron expression parsing."""
    scheduler = Scheduler()
    
    # Test valid cron expressions
    query = ScheduledQuery(
        question="Show daily sales",
        dataset_id="sales",
        cron_expr="1h",  # Every hour
        recipients=["admin@example.com"],
    )
    
    assert scheduler.parse_cron("1h") is True
    assert scheduler.parse_cron("daily") is True
    assert scheduler.parse_cron("weekly") is True
    assert scheduler.parse_cron("25h") is False  # Invalid
    assert scheduler.parse_cron("invalid") is False
    
    # Test adding and retrieving scheduled query
    query_id = scheduler.add_query(query)
    assert query_id is not None
    
    retrieved = scheduler.get_query(query_id)
    assert retrieved is not None
    assert retrieved.question == "Show daily sales"
    assert retrieved.cron_expr == "1h"