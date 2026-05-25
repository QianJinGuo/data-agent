"""Agent state for the Marketing Strategy LangGraph pipeline."""
from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage


class MarketingAgentState(TypedDict, total=False):
    """Shared state across all marketing graph nodes."""

    messages: list[BaseMessage]
    campaign_objective: str
    target_audience: Optional[dict]  # audience_result from CDP
    audience_insights: Optional[str]
    proposed_plans: list[dict]
    selected_plan: Optional[dict]
    generated_strategy: Optional[dict]
    outreach_tasks: list[dict]
    final_answer: str
    error: Optional[str]