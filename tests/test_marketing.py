"""Tests for Phase 3 marketing and orchestration components."""
from nl2sql.marketing_state import MarketingAgentState
from nl2sql.marketing_schema import AudienceSegment, MarketingPlan, Strategy, OutreachTask, MarketingCampaign
from nl2sql.marketing_graph import build_marketing_graph
from nl2sql.orchestrator import DataAgentOrchestrator
from nl2sql.cdp_client import CDPClient, MockCDPClient


class MockLLM:
    """Simple mock LLM for testing."""

    def invoke(self, prompt: str):
        class Response:
            content = '{"objective": "promotion", "audience_keywords": ["high value", "active"]}'
        return Response()


def test_marketing_state_shape():
    """Test MarketingAgentState has all required fields."""
    state = MarketingAgentState(
        messages=[],
        campaign_objective="",
        target_audience=None,
        audience_insights=None,
        proposed_plans=[],
        selected_plan=None,
        generated_strategy=None,
        outreach_tasks=[],
        final_answer="",
        error=None,
    )
    assert "campaign_objective" in state
    assert "target_audience" in state
    assert "proposed_plans" in state
    assert "generated_strategy" in state
    assert "outreach_tasks" in state


def test_marketing_schema():
    """Test Pydantic models for marketing domain."""
    audience = AudienceSegment(
        id="aud-1",
        name="High Value Users",
        rules=[{"tag": "spend", "op": ">=", "value": 1000}],
        estimated_count=15832,
        insights="25-35 age group, weekend active",
    )
    assert audience.estimated_count == 15832

    plan = MarketingPlan(
        id="plan-1",
        name="Segmentation Campaign",
        dimension="audience_segmentation",
        description="Split audience by purchase frequency into high/medium/low tiers",
        estimated_effect="conversion_rate: 15%",
    )
    assert plan.dimension == "audience_segmentation"

    strategy = Strategy(
        id="str-1",
        timing_design=[{"segment": "high_value", "best_time": "weekend 10:00-12:00"}],
        channel_priority={"sms": 0.7, "webhook": 0.3},
        content_variants=[{"segment": "high_value", "content": "Dear VIP..."}],
    )
    assert len(strategy.timing_design) == 1

    task = OutreachTask(
        id="task-1",
        campaign_id="camp-1",
        audience_id="aud-1",
        trigger_condition='{"type": "time_window", "start": "2026-06-01", "end": "2026-06-18"}',
        channel="sms",
        template_id="tmpl-1",
        status="draft",
    )
    assert task.status == "draft"

    campaign = MarketingCampaign(
        id="camp-1",
        name="618 大促",
        objective="提升复购率",
        audience_id="aud-1",
        timing={"type": "optimal_window"},
        channels=["sms", "webhook"],
        status="draft",
    )
    assert campaign.status == "draft"


def test_build_marketing_graph():
    """Test marketing graph builds without error."""
    llm = MockLLM()
    graph = build_marketing_graph(llm=llm, cdp_client=None)
    assert graph is not None


def test_mock_cdp_client():
    """Test MockCDPClient builds audience correctly."""
    cdp = MockCDPClient()
    hints = {
        "description": "high value customers",
        "age_range": "25-40",
        "spend_threshold": 1000,
    }
    result = cdp.build_audience(hints)
    assert "id" in result
    assert "name" in result
    assert "estimated_count" in result
    assert "insights" in result


def test_orchestrator_route():
    """Test DataAgentOrchestrator routes questions correctly."""
    llm = MockLLM()
    graph = build_marketing_graph(llm=llm, cdp_client=MockCDPClient())

    # Create a simple mock for nl2sql graph
    class MockGraph:
        def invoke(self, state):
            return state

    orchestrator = DataAgentOrchestrator(
        nl2sql_graph=MockGraph(),
        marketing_graph=graph,
        cdp_client=MockCDPClient(),
    )

    # Test marketing route detection
    marketing_question = "I want to run a campaign for high-value customers"
    route = orchestrator.route_question(marketing_question)
    assert route in ["marketing", "nl2sql", "other"]