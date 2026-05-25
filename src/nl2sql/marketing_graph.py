"""LangGraph pipeline definition for Marketing Strategy Agent."""
from langgraph.graph import StateGraph, END
from nl2sql.marketing_state import MarketingAgentState


def build_marketing_graph(llm, cdp_client=None):
    """Build and return the compiled Marketing Strategy StateGraph.

    llm: pre-built LLM instance
    cdp_client: optional CDP client for audience building
    """
    from nl2sql import marketing_nodes as nodes

    g = StateGraph(MarketingAgentState)

    def parse_objective_node(state):
        return nodes.parse_objective(state, llm)

    def audience_build_node(state):
        return nodes.audience_build(state, llm, cdp_client)

    def plan_generate_node(state):
        return nodes.plan_generate(state, llm)

    def strategy_generate_node(state):
        return nodes.strategy_generate(state, llm)

    def task_config_node(state):
        return nodes.task_config(state)

    g.add_node("parse_objective", parse_objective_node)
    g.add_node("audience_build", audience_build_node)
    g.add_node("plan_generate", plan_generate_node)
    g.add_node("strategy_generate", strategy_generate_node)
    g.add_node("task_config", task_config_node)

    # Sequential flow: straight line
    g.add_edge("parse_objective", "audience_build")
    g.add_edge("audience_build", "plan_generate")
    g.add_edge("plan_generate", "strategy_generate")
    g.add_edge("strategy_generate", "task_config")
    g.add_edge("task_config", END)

    g.set_entry_point("parse_objective")
    return g.compile()