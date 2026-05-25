"""Agent state for the NL2SQL LangGraph pipeline."""
from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """Shared state across all graph nodes."""

    messages: list[BaseMessage]
    intent: str
    sql: str
    query_result: Optional[dict]
    attribution_result: Optional[dict]
    chart_type: str
    final_answer: str
    error: Optional[str]