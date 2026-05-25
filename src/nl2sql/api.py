"""FastAPI REST API for Data Agent."""
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

app = FastAPI(title="Data Agent API", version="0.1.0")

# In-memory storage for demo purposes
_campaigns = {}
_plans = {}
_strategies = {}
_tasks = []


# Request/Response Models
class QueryRequest(BaseModel):
    """Request body for NL2SQL query endpoint."""

    question: str
    conversation_id: Optional[str] = None
    dataset_ids: Optional[list[str]] = None


class QueryResponse(BaseModel):
    """Response body for NL2SQL query endpoint."""

    final_answer: str
    sql: str
    query_result: Optional[dict] = None
    chart_type: str = "table"
    intent: str = "unknown"


class CampaignRequest(BaseModel):
    """Request body for creating marketing campaign."""

    objective: str
    audience_description: str
    timing: Optional[dict] = Field(default_factory=dict)
    channels: Optional[list[str]] = Field(default_factory=list)


class CampaignResponse(BaseModel):
    """Response body for marketing campaign creation."""

    campaign_id: str
    audience_result: Optional[dict] = None
    proposed_plans: list[dict] = Field(default_factory=list)


class ApplyPlanRequest(BaseModel):
    """Request body for applying plan to create strategy."""

    channels: list[str] = Field(default_factory=list)
    content: Optional[dict] = None


class StrategyResponse(BaseModel):
    """Response body for strategy creation."""

    strategy_id: str
    timing_design: list[dict] = Field(default_factory=list)
    content_variants: list[dict] = Field(default_factory=list)


class TaskResponse(BaseModel):
    """Response body for task listing."""

    tasks: list[dict]
    total: int


class HealthResponse(BaseModel):
    """Response body for health check."""

    status: str
    version: str


# Mock LLM flag - set to True when LLM is not configured
MOCK_MODE = True


def _get_orchestrator():
    """Get or create orchestrator instance."""
    try:
        from nl2sql.orchestrator import DataAgentOrchestrator
        from nl2sql.cdp_client import MockCDPClient

        return DataAgentOrchestrator(
            cdp_client=MockCDPClient(),
            llm_provider="openai",
            llm_model="gpt-4o",
        )
    except Exception:
        return None


@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    """Run NL2SQL query.

    Args:
        request: Query request with question and optional parameters.

    Returns:
        Query response with final_answer, sql, query_result, chart_type, intent.
    """
    if MOCK_MODE:
        # Return mock response when LLM not configured
        return QueryResponse(
            final_answer=f"Mock answer for: {request.question}",
            sql="SELECT * FROM mock_table WHERE 1=1",
            query_result={"rows": [], "columns": []},
            chart_type="table",
            intent="select",
        )

    orchestrator = _get_orchestrator()
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    result = orchestrator.run_nl2sql(
        question=request.question,
        conversation_id=request.conversation_id,
        datasets=request.dataset_ids,
    )

    return QueryResponse(
        final_answer=result.get("final_answer", ""),
        sql=result.get("sql", ""),
        query_result=result.get("query_result"),
        chart_type=result.get("chart_type", "table"),
        intent=result.get("intent", "unknown"),
    )


@app.post("/marketing/campaigns", response_model=CampaignResponse)
async def create_campaign(request: CampaignRequest):
    """Create marketing campaign.

    Args:
        request: Campaign request with objective, audience, timing, channels.

    Returns:
        Campaign response with campaign_id, audience_result, proposed_plans.
    """
    campaign_id = str(uuid.uuid4())

    if MOCK_MODE:
        # Return mock response when LLM not configured
        audience_result = {
            "id": str(uuid.uuid4()),
            "name": f"Audience for {request.objective[:30]}",
            "rules": [],
            "estimated_count": 10000,
            "insights": "Mock audience insights based on description.",
        }

        proposed_plans = [
            {
                "id": str(uuid.uuid4()),
                "name": "Plan A: Multi-channel Approach",
                "dimension": "渠道",
                "description": "Leverage multiple channels for maximum reach.",
                "estimated_effect": "High engagement expected.",
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Plan B: Focused Targeting",
                "dimension": "人群",
                "description": "Concentrate on highly targeted segment.",
                "estimated_effect": "Better conversion rate.",
            },
        ]

        _campaigns[campaign_id] = {
            "id": campaign_id,
            "objective": request.objective,
            "audience_description": request.audience_description,
            "timing": request.timing,
            "channels": request.channels,
            "created_at": datetime.now().isoformat(),
        }

        return CampaignResponse(
            campaign_id=campaign_id,
            audience_result=audience_result,
            proposed_plans=proposed_plans,
        )

    orchestrator = _get_orchestrator()
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    result = orchestrator.run_marketing(
        objective=request.objective,
        audience_hints=request.audience_description,
    )

    # Store campaign
    _campaigns[campaign_id] = {
        "id": campaign_id,
        "objective": request.objective,
        "audience_description": request.audience_description,
        "audience_result": result.get("audience_result"),
        "timing": request.timing,
        "channels": request.channels,
        "created_at": datetime.now().isoformat(),
    }

    # Store plans
    for plan in result.get("proposed_plans", []):
        plan_id = plan.get("id", str(uuid.uuid4()))
        _plans[plan_id] = plan

    return CampaignResponse(
        campaign_id=campaign_id,
        audience_result=result.get("audience_result"),
        proposed_plans=result.get("proposed_plans", []),
    )


@app.post("/marketing/plans/{plan_id}/apply", response_model=StrategyResponse)
async def apply_plan(plan_id: str, request: ApplyPlanRequest):
    """Apply plan to create strategy.

    Args:
        plan_id: ID of the plan to apply.
        request: Strategy configuration with channels and content.

    Returns:
        Strategy response with strategy_id, timing_design, content_variants.
    """
    if plan_id not in _plans:
        if MOCK_MODE:
            # Return mock strategy in mock mode
            strategy_id = str(uuid.uuid4())
            timing_design = [
                {"phase": "pre_launch", "timing": "T-7 days", "action": "Content preparation"},
                {"phase": "launch", "timing": "T-0", "action": "Campaign launch"},
                {"phase": "optimize", "timing": "T+3 days", "action": "Performance review"},
                {"phase": "close", "timing": "T+7 days", "action": "Campaign wrap-up"},
            ]
            content_variants = [
                {"variant": "A", "channel": "email", "template": "promo_email_v1"},
                {"variant": "B", "channel": "social", "template": "social_post_v1"},
                {"variant": "C", "channel": "push", "template": "push_notification_v1"},
            ]

            _strategies[strategy_id] = {
                "id": strategy_id,
                "plan_id": plan_id,
                "channels": request.channels,
                "content": request.content,
                "timing_design": timing_design,
                "content_variants": content_variants,
            }

            return StrategyResponse(
                strategy_id=strategy_id,
                timing_design=timing_design,
                content_variants=content_variants,
            )

        raise HTTPException(status_code=404, detail="Plan not found")

    plan = _plans[plan_id]

    # In a real implementation, this would invoke the marketing graph
    strategy_id = str(uuid.uuid4())
    timing_design = [
        {"phase": "phase_1", "timing": "Week 1", "action": plan.get("description", "Execute phase 1")},
        {"phase": "phase_2", "timing": "Week 2", "action": "Monitor and optimize"},
        {"phase": "phase_3", "timing": "Week 3", "action": "Scale successful channels"},
    ]
    content_variants = [
        {"variant": "A", "channel": channel, "template": f"template_{channel}"}
        for channel in request.channels
    ]

    _strategies[strategy_id] = {
        "id": strategy_id,
        "plan_id": plan_id,
        "channels": request.channels,
        "content": request.content,
        "timing_design": timing_design,
        "content_variants": content_variants,
    }

    return StrategyResponse(
        strategy_id=strategy_id,
        timing_design=timing_design,
        content_variants=content_variants,
    )


@app.get("/marketing/tasks", response_model=TaskResponse)
async def list_tasks():
    """List all outreach tasks.

    Returns:
        List of tasks with total count.
    """
    # In real implementation, tasks would come from orchestrator state
    if not _tasks and MOCK_MODE:
        _tasks.extend(
            [
                {
                    "id": str(uuid.uuid4()),
                    "campaign_id": "mock-campaign-1",
                    "audience_id": "mock-audience-1",
                    "trigger_condition": "immediate",
                    "channel": "email",
                    "template_id": "welcome_email",
                    "status": "pending",
                },
                {
                    "id": str(uuid.uuid4()),
                    "campaign_id": "mock-campaign-1",
                    "audience_id": "mock-audience-1",
                    "trigger_condition": "24h_after_signup",
                    "channel": "push",
                    "template_id": "onboarding_push",
                    "status": "pending",
                },
            ]
        )

    return TaskResponse(tasks=_tasks, total=len(_tasks))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.

    Returns:
        Health status with API version.
    """
    return HealthResponse(status="healthy", version="0.1.0")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
