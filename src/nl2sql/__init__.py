"""NL2SQL Data Agent - LangGraph-based Natural Language to SQL Pipeline."""

from nl2sql.schema import Dataset, SemanticModel, Metric, Dimension
from nl2sql.state import AgentState
from nl2sql.graph import build_graph
from nl2sql.llm import build_llm

# Phase 3: Marketing and Orchestrator
from nl2sql.marketing_state import MarketingAgentState
from nl2sql.marketing_schema import (
    AudienceSegment,
    MarketingPlan,
    Strategy,
    OutreachTask,
    MarketingCampaign,
)
from nl2sql.marketing_graph import build_marketing_graph
from nl2sql.orchestrator import DataAgentOrchestrator
from nl2sql.cdp_client import CDPClient, MockCDPClient

__version__ = "0.1.0"
__all__ = [
    # Schema
    "Dataset",
    "SemanticModel",
    "Metric",
    "Dimension",
    # State
    "AgentState",
    "MarketingAgentState",
    # Graphs
    "build_graph",
    "build_marketing_graph",
    # LLM
    "build_llm",
    # Orchestrator
    "DataAgentOrchestrator",
    # CDP
    "CDPClient",
    "MockCDPClient",
    # Marketing schemas
    "AudienceSegment",
    "MarketingPlan",
    "Strategy",
    "OutreachTask",
    "MarketingCampaign",
]