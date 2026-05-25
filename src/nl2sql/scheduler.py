"""Scheduler for periodic query execution and delivery."""
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


@dataclass
class ScheduledQuery:
    """A query scheduled for periodic execution."""

    question: str
    dataset_id: str
    cron_expr: str
    recipients: List[str] = field(default_factory=list)
    owner: str = ""
    last_run: Optional[datetime] = None
    enabled: bool = True
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Generate query_id if not provided."""
        if not self.query_id:
            self.query_id = str(uuid.uuid4())


class Scheduler:
    """Manages scheduled periodic queries.

    Supports cron-like expressions for timing:
    - "1h", "2h", "6h", "12h": hourly intervals
    - "daily": once per day (midnight)
    - "weekly": once per week (Monday midnight)
    - Custom cron-like expressions for advanced scheduling
    """

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduled_queries: List[ScheduledQuery] = []
        self._running = False
        self._last_check: Optional[datetime] = None

    def add_query(self, sq: ScheduledQuery) -> str:
        """Add a new scheduled query.

        Args:
            sq: ScheduledQuery instance

        Returns:
            query_id of the added query
        """
        if not self.parse_cron(sq.cron_expr):
            raise ValueError(f"Invalid cron expression: {sq.cron_expr}")

        self.scheduled_queries.append(sq)
        logger.info(
            f"Added scheduled query {sq.query_id}: '{sq.question}' "
            f"with schedule '{sq.cron_expr}'"
        )
        return sq.query_id

    def remove_query(self, query_id: str) -> bool:
        """Remove a scheduled query.

        Args:
            query_id: ID of the query to remove

        Returns:
            True if query was found and removed, False otherwise
        """
        initial_count = len(self.scheduled_queries)
        self.scheduled_queries = [
            sq for sq in self.scheduled_queries if sq.query_id != query_id
        ]
        removed = len(self.scheduled_queries) < initial_count

        if removed:
            logger.info(f"Removed scheduled query {query_id}")

        return removed

    def get_query(self, query_id: str) -> Optional[ScheduledQuery]:
        """Get a scheduled query by ID.

        Args:
            query_id: Query identifier

        Returns:
            ScheduledQuery if found, None otherwise
        """
        for sq in self.scheduled_queries:
            if sq.query_id == query_id:
                return sq
        return None

    def list_queries(self, enabled_only: bool = False) -> List[ScheduledQuery]:
        """List all scheduled queries.

        Args:
            enabled_only: If True, return only enabled queries

        Returns:
            List of ScheduledQuery instances
        """
        if enabled_only:
            return [sq for sq in self.scheduled_queries if sq.enabled]
        return self.scheduled_queries.copy()

    def enable_query(self, query_id: str) -> bool:
        """Enable a scheduled query.

        Args:
            query_id: Query identifier

        Returns:
            True if query was found and enabled, False otherwise
        """
        sq = self.get_query(query_id)
        if sq:
            sq.enabled = True
            logger.info(f"Enabled scheduled query {query_id}")
            return True
        return False

    def disable_query(self, query_id: str) -> bool:
        """Disable a scheduled query.

        Args:
            query_id: Query identifier

        Returns:
            True if query was found and disabled, False otherwise
        """
        sq = self.get_query(query_id)
        if sq:
            sq.enabled = False
            logger.info(f"Disabled scheduled query {query_id}")
            return True
        return False

    def parse_cron(self, cron_expr: str) -> bool:
        """Validate a cron expression.

        Supported formats:
        - "1h", "2h", "3h", ..., "23h": hourly intervals
        - "daily": once per day
        - "weekly": once per week

        Args:
            cron_expr: Cron expression string

        Returns:
            True if valid, False otherwise
        """
        cron_expr = cron_expr.strip().lower()

        # Hourly patterns: "1h", "2h", ..., "23h"
        if cron_expr.endswith("h"):
            try:
                hours = int(cron_expr[:-1])
                return 1 <= hours <= 23
            except ValueError:
                return False

        # Daily pattern
        if cron_expr == "daily":
            return True

        # Weekly pattern
        if cron_expr == "weekly":
            return True

        return False

    def _parse_cron_to_interval(self, cron_expr: str) -> Optional[timedelta]:
        """Parse cron expression to time interval.

        Args:
            cron_expr: Cron expression string

        Returns:
            timedelta interval, or None for daily/weekly (checked by date)
        """
        cron_expr = cron_expr.strip().lower()

        if cron_expr.endswith("h"):
            try:
                hours = int(cron_expr[:-1])
                return timedelta(hours=hours)
            except ValueError:
                return None

        if cron_expr == "daily":
            return timedelta(days=1)

        if cron_expr == "weekly":
            return timedelta(weeks=1)

        return None

    def _is_due(self, sq: ScheduledQuery, now: datetime) -> bool:
        """Check if a scheduled query is due to run.

        Args:
            sq: ScheduledQuery instance
            now: Current datetime

        Returns:
            True if query should run now, False otherwise
        """
        if not sq.enabled:
            return False

        if sq.last_run is None:
            return True

        cron_expr = sq.cron_expr.strip().lower()

        # For hourly intervals, check by elapsed time
        if cron_expr.endswith("h"):
            interval = self._parse_cron_to_interval(cron_expr)
            if interval:
                return now - sq.last_run >= interval
            return False

        # For daily, check if it's a new day since last run
        if cron_expr == "daily":
            return (
                now.date() > sq.last_run.date()
            )

        # For weekly, check if it's a new week (Monday)
        if cron_expr == "weekly":
            # Monday is weekday 0 in Python's weekday()
            return (
                now.date() > sq.last_run.date()
                and now.weekday() == 0
            )

        return False

    def check_and_run(
        self,
        llm: Any,
        db_connector: Any,
        conversation_manager: Any,
    ) -> Dict[str, Any]:
        """Check all scheduled queries and run those that are due.

        Args:
            llm: Language model for query generation and interpretation
            db_connector: Database connector for executing queries
            conversation_manager: Conversation manager for context

        Returns:
            Dictionary with run results: {query_id: result, ...}
        """
        now = datetime.now()
        results = {}
        due_queries = []

        # Identify due queries
        for sq in self.scheduled_queries:
            if self._is_due(sq, now):
                due_queries.append(sq)

        if not due_queries:
            return {"checked": len(self.scheduled_queries), "executed": 0}

        logger.info(f"Found {len(due_queries)} queries due for execution")

        # Execute each due query
        for sq in due_queries:
            try:
                result = self._execute_scheduled_query(
                    sq,
                    llm,
                    db_connector,
                    conversation_manager,
                )
                results[sq.query_id] = result
                sq.last_run = now

            except Exception as e:
                logger.error(f"Failed to execute scheduled query {sq.query_id}: {e}")
                results[sq.query_id] = {
                    "success": False,
                    "error": str(e),
                }

        return {
            "checked": len(self.scheduled_queries),
            "executed": len(due_queries),
            "results": results,
        }

    def _execute_scheduled_query(
        self,
        sq: ScheduledQuery,
        llm: Any,
        db_connector: Any,
        conversation_manager: Any,
    ) -> Dict[str, Any]:
        """Execute a single scheduled query.

        Args:
            sq: ScheduledQuery instance
            llm: Language model
            db_connector: Database connector
            conversation_manager: Conversation manager

        Returns:
            Execution result dictionary
        """
        logger.info(f"Executing scheduled query: {sq.question}")

        # For now, we generate SQL from the question and execute it
        # This leverages the existing nl2sql pipeline
        from nl2sql.graph import build_graph
        from nl2sql.schema import Dataset

        try:
            # Import here to avoid circular imports
            from nl2sql.multi_dataset import MultiDatasetManager

            # Get dataset schema
            multi_manager = getattr(db_connector, 'multi_dataset_manager', None)
            if multi_manager:
                dataset = multi_manager.get_dataset(sq.dataset_id)
            else:
                dataset = Dataset(
                    dataset_id=sq.dataset_id,
                    name=sq.dataset_id,
                    table_name=sq.dataset_id,
                )

            if not dataset:
                return {
                    "success": False,
                    "error": f"Dataset {sq.dataset_id} not found",
                }

            # Build and run the graph
            graph = build_graph(dataset=dataset, llm=llm)

            initial_state = {
                "messages": [HumanMessage(content=sq.question)],
                "dataset_id": sq.dataset_id,
            }

            final_state = graph.invoke(initial_state)

            query_result = final_state.get("query_result")
            final_answer = final_state.get("final_answer", "No answer generated")

            return {
                "success": True,
                "question": sq.question,
                "query_result": query_result,
                "answer": final_answer,
                "recipients": sq.recipients,
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "question": sq.question,
                "error": str(e),
            }

    def run_forever(
        self,
        interval: float = 60.0,
        llm: Optional[Any] = None,
        db_connector: Optional[Any] = None,
        conversation_manager: Optional[Any] = None,
    ) -> None:
        """Run the scheduler loop indefinitely.

        Continuously checks and executes due queries at the specified interval.

        Args:
            interval: Sleep interval between checks in seconds (default 60)
            llm: Language model for query execution
            db_connector: Database connector
            conversation_manager: Conversation manager
        """
        self._running = True
        logger.info(f"Scheduler started with {interval}s interval")

        while self._running:
            try:
                if llm and db_connector and conversation_manager:
                    results = self.check_and_run(
                        llm=llm,
                        db_connector=db_connector,
                        conversation_manager=conversation_manager,
                    )
                    if results.get("executed", 0) > 0:
                        logger.info(
                            f"Scheduler cycle complete: "
                            f"checked={results['checked']}, executed={results['executed']}"
                        )

                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(interval)  # Continue despite errors

        logger.info("Scheduler stopped")

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        logger.info("Scheduler stop requested")

    def is_running(self) -> bool:
        """Check if scheduler is running.

        Returns:
            True if running, False otherwise
        """
        return self._running