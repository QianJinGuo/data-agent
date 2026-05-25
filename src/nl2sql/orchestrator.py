"""Data Agent Orchestrator - single entry point for all Data Agent operations."""
from typing import Optional, Literal
from nl2sql.graph import build_graph
from nl2sql.marketing_graph import build_marketing_graph
from nl2sql.cdp_client import CDPClient
from nl2sql.llm import build_llm


class DataAgentOrchestrator:
    """Orchestrates NL2SQL and Marketing strategy workflows.

    The orchestrator is the single entry point for all Data Agent operations,
    providing routing between NL2SQL queries and Marketing campaigns.
    """

    def __init__(
        self,
        nl2sql_graph=None,
        marketing_graph=None,
        cdp_client: Optional[CDPClient] = None,
        llm=None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o",
    ):
        """Initialize the Data Agent Orchestrator.

        Args:
            nl2sql_graph: Pre-compiled NL2SQL graph (optional, will build if None).
            marketing_graph: Pre-compiled marketing graph (optional, will build if None).
            cdp_client: CDP client for audience building (optional).
            llm: Pre-built LLM instance (optional).
            llm_provider: LLM provider for building new LLM.
            llm_model: LLM model name.
        """
        self.llm = llm
        self.llm_provider = llm_provider
        self.llm_model = llm_model

        if self.llm is None:
            self.llm = build_llm(provider=llm_provider, model=llm_model)

        self.nl2sql_graph = nl2sql_graph
        self.marketing_graph = marketing_graph
        self.cdp_client = cdp_client

    def _ensure_nl2sql_graph(self):
        """Ensure NL2SQL graph is initialized."""
        if self.nl2sql_graph is None:
            self.nl2sql_graph = build_graph(
                dataset=None,
                llm=self.llm,
                llm_provider=self.llm_provider,
                llm_model=self.llm_model,
            )

    def _ensure_marketing_graph(self):
        """Ensure marketing graph is initialized."""
        if self.marketing_graph is None:
            self.marketing_graph = build_marketing_graph(
                llm=self.llm, cdp_client=self.cdp_client
            )

    def route_question(self, question: str) -> str:
        """Classify question type into nl2sql/marketing/other using LLM.

        Args:
            question: The user's question or request.

        Returns:
            Question type: "nl2sql", "marketing", or "other".
        """
        prompt = f"""Classify the following user question into one of these categories:
- "nl2sql": Questions asking about data analysis, database queries, metrics, trends, SQL generation
- "marketing": Questions about marketing campaigns, audience building, strategy, outreach
- "other": Questions that don't fit either category

Question: {question}

Respond with only the category name: nl2sql, marketing, or other"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.lower().strip() if hasattr(response, "content") else str(response).lower()

            if "marketing" in content:
                return "marketing"
            elif "nl2sql" in content or "data" in content or "sql" in content or "query" in content:
                return "nl2sql"
            else:
                return "other"
        except Exception:
            # Default to nl2sql if LLM call fails
            return "nl2sql"

    def run_nl2sql(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        datasets=None,
    ) -> dict:
        """Run NL2SQL query workflow.

        Args:
            question: The natural language question to convert to SQL.
            conversation_id: Optional conversation identifier for context.
            datasets: Optional list of dataset IDs to query against.

        Returns:
            Dict containing final_answer, sql, query_result, chart_type, intent.
        """
        self._ensure_nl2sql_graph()

        initial_state = {
            "messages": [],
            "intent": "",
            "sql": "",
            "query_result": None,
            "attribution_result": None,
            "chart_type": "",
            "final_answer": "",
            "error": None,
            "conversation_id": conversation_id or "",
            "datasets": datasets or [],
            "anomaly_result": None,
            "detection_result": None,
        }

        try:
            result = self.nl2sql_graph.invoke(initial_state)
            return {
                "final_answer": result.get("final_answer", ""),
                "sql": result.get("sql", ""),
                "query_result": result.get("query_result"),
                "chart_type": result.get("chart_type", "table"),
                "intent": result.get("intent", "unknown"),
            }
        except Exception as e:
            return {
                "final_answer": f"Error processing query: {str(e)}",
                "sql": "",
                "query_result": None,
                "chart_type": "table",
                "intent": "error",
            }

    def run_marketing(self, objective: str, audience_hints: str) -> dict:
        """Run marketing strategy workflow.

        Args:
            objective: The marketing campaign objective.
            audience_hints: Natural language description of target audience.

        Returns:
            Dict containing campaign_id, audience_result, proposed_plans.
        """
        self._ensure_marketing_graph()

        # Parse audience hints into structured format
        hints = self._parse_audience_hints(audience_hints)

        initial_state = {
            "messages": [],
            "campaign_objective": objective,
            "target_audience": None,
            "audience_insights": None,
            "proposed_plans": [],
            "selected_plan": None,
            "generated_strategy": None,
            "outreach_tasks": [],
            "final_answer": "",
            "error": None,
            "_audience_hints": hints,
        }

        try:
            result = self.marketing_graph.invoke(initial_state)
            return {
                "campaign_id": result.get("target_audience", {}).get("id", ""),
                "audience_result": result.get("target_audience"),
                "proposed_plans": result.get("proposed_plans", []),
            }
        except Exception as e:
            return {
                "campaign_id": "",
                "audience_result": None,
                "proposed_plans": [],
                "error": str(e),
            }

    def run(self, question: str) -> dict:
        """Auto-detect question type and run appropriate workflow.

        Args:
            question: The user's question or request.

        Returns:
            Dict with question type and workflow result.
        """
        question_type = self.route_question(question)

        if question_type == "marketing":
            # For marketing questions, extract objective and audience hints
            # This is a simplified extraction; in production, use LLM extraction
            return {
                "question_type": "marketing",
                "result": self.run_marketing(
                    objective=question,
                    audience_hints="general audience",
                ),
            }
        elif question_type == "nl2sql":
            return {
                "question_type": "nl2sql",
                "result": self.run_nl2sql(question=question),
            }
        else:
            return {
                "question_type": "other",
                "result": {
                    "final_answer": "I can help with data analysis queries (NL2SQL) or marketing campaign strategies. Please rephrase your question.",
                },
            }

    def _parse_audience_hints(self, hints_text: str) -> dict:
        """Parse natural language audience hints into structured format.

        Args:
            hints_text: Natural language description of audience.

        Returns:
            Structured hints dictionary.
        """
        # Simple keyword-based parsing
        hints = {}

        lower_text = hints_text.lower()

        # Extract demographics
        demographics = {}
        if "age" in lower_text:
            # Try to find age ranges
            if "18-25" in lower_text or "young" in lower_text:
                demographics["age"] = "18-25"
            elif "25-35" in lower_text or "young adult" in lower_text:
                demographics["age"] = "25-35"
            elif "35-45" in lower_text or "middle" in lower_text:
                demographics["age"] = "35-45"
            elif "45+" in lower_text or "older" in lower_text or "senior" in lower_text:
                demographics["age"] = "45+"
        if "male" in lower_text or "men" in lower_text:
            demographics["gender"] = "male"
        elif "female" in lower_text or "women" in lower_text:
            demographics["gender"] = "female"

        if demographics:
            hints["demographics"] = demographics

        # Extract behaviors
        behaviors = []
        behavior_keywords = ["purchase", "browse", "signup", "engag", "click", "view"]
        for keyword in behavior_keywords:
            if keyword in lower_text:
                behaviors.append(keyword)

        if behaviors:
            hints["behaviors"] = behaviors

        # Extract interests
        interests = []
        interest_keywords = ["tech", "fashion", "sport", "food", "travel", "music"]
        for keyword in interest_keywords:
            if keyword in lower_text:
                interests.append(keyword)

        if interests:
            hints["interests"] = interests

        return hints
