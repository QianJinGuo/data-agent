"""LangGraph pipeline definition."""
from langgraph.graph import StateGraph, END
from nl2sql.state import AgentState
from nl2sql.llm import build_llm
from nl2sql.schema import Dataset
from nl2sql import nodes


def build_graph(dataset: Dataset, llm=None, llm_provider: str = "openai", llm_model: str = "gpt-4o"):
    """Build and return the compiled NL2SQL StateGraph.

    dataset: semantic model dataset
    llm: pre-built LLM instance (optional)
    llm_provider: "openai" | "anthropic" | "local"
    llm_model: model name
    """
    if llm is None:
        llm = build_llm(provider=llm_provider, model=llm_model)  # type: ignore[arg-type]

    g = StateGraph(AgentState)

    def classify_node(state):
        return nodes.intent_classify(state, llm, dataset)

    def generate_node(state):
        return nodes.sql_generate(state, llm, dataset)

    def execute_node(state):
        return nodes.sql_execute(state, dataset)

    def attribute_node(state):
        return nodes.attribution(state)

    def interpret_node(state):
        return nodes.interpret(state, llm, dataset)

    def detect_anomaly_node(state):
        return nodes.detect_anomaly(state)

    g.add_node("intent_classify", classify_node)
    g.add_node("sql_generate", generate_node)
    g.add_node("sql_execute", execute_node)
    g.add_node("attribution", attribute_node)
    g.add_node("interpret", interpret_node)
    g.add_node("detect_anomaly", detect_anomaly_node)

    # Normal flow
    g.add_edge("intent_classify", "sql_generate")
    g.add_edge("sql_generate", "sql_execute")

    # Conditional: if error in sql_execute, skip attribution and go to interpret
    def route_after_execute(state):
        if state.get("error"):
            return "interpret"
        return "attribution"

    g.add_conditional_edges("sql_execute", route_after_execute)
    g.add_edge("attribution", "interpret")
    g.add_edge("interpret", "detect_anomaly")
    g.add_edge("detect_anomaly", END)

    g.set_entry_point("intent_classify")
    return g.compile()