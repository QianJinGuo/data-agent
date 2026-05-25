"""Conversation manager for multi-turn dialogue handling."""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


@dataclass
class ConversationConfig:
    """Configuration for conversation management."""

    max_messages: int = 10
    max_tokens: int = 4000
    summary_trigger_ratio: float = 0.8


class ConversationManager:
    """Manages conversation history for multi-turn dialogues.

    Provides functionality for:
    - Storing and retrieving message history per conversation
    - Automatic summarization when history grows too long
    - Conversation lifecycle management
    """

    def __init__(
        self,
        config: Optional[ConversationConfig] = None,
    ):
        """Initialize the conversation manager.

        Args:
            config: Conversation configuration (uses defaults if not provided)
        """
        self.config = config or ConversationConfig()
        self.conversations: Dict[str, List[BaseMessage]] = {}
        self._token_counts: Dict[str, int] = {}

    def get_history(self, conversation_id: str) -> List[BaseMessage]:
        """Get message history for a conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            List of messages in chronological order
        """
        return self.conversations.get(conversation_id, [])

    def add_message(
        self,
        conversation_id: str,
        message: BaseMessage,
    ) -> None:
        """Add a message to conversation history.

        Args:
            conversation_id: Unique conversation identifier
            message: Message to add (HumanMessage, AIMessage, etc.)
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
            self._token_counts[conversation_id] = 0

        self.conversations[conversation_id].append(message)
        self._token_counts[conversation_id] += self._estimate_tokens(message)

        logger.debug(
            f"Added {message.__class__.__name__} to conversation {conversation_id}. "
            f"Total messages: {len(self.conversations[conversation_id])}"
        )

    def get_message_count(self, conversation_id: str) -> int:
        """Get number of messages in a conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Number of messages, or 0 if conversation doesn't exist
        """
        return len(self.conversations.get(conversation_id, []))

    def summarize_if_needed(
        self,
        conversation_id: str,
        llm: BaseChatModel,
        max_messages: Optional[int] = None,
    ) -> bool:
        """Conditionally summarize conversation history if it exceeds threshold.

        Summarizes the conversation when:
        - Message count exceeds max_messages
        - Total tokens approach the configured limit

        Args:
            conversation_id: Unique conversation identifier
            llm: Language model for generating summary
            max_messages: Override for maximum messages before summarization

        Returns:
            True if summarization was performed, False otherwise
        """
        if conversation_id not in self.conversations:
            return False

        messages = self.conversations[conversation_id]
        max_msg = max_messages or self.config.max_messages

        if len(messages) <= max_msg:
            return False

        # Check if we should summarize based on token ratio
        token_ratio = (
            self._token_counts.get(conversation_id, 0) / self.config.max_tokens
        )
        if token_ratio < self.config.summary_trigger_ratio and len(messages) < max_msg * 2:
            return False

        try:
            self._summarize_conversation(conversation_id, llm)
            return True
        except Exception as e:
            logger.warning(f"Failed to summarize conversation {conversation_id}: {e}")
            return False

    def _summarize_conversation(
        self,
        conversation_id: str,
        llm: BaseChatModel,
    ) -> None:
        """Generate and apply conversation summary.

        Replaces full message history with a condensed summary plus
        recent messages to stay within token limits.

        Args:
            conversation_id: Unique conversation identifier
            llm: Language model for generating summary
        """
        messages = self.conversations[conversation_id]
        if not messages:
            return

        # Build prompt for summarization
        history_text = self._format_messages_for_summary(messages)

        summary_prompt = f"""Summarize the following conversation concisely.
Focus on:
1. Main topics and questions discussed
2. Key insights, answers, or conclusions reached
3. Any pending follow-up questions or actions

Conversation:
{history_text}

Provide a summary in 2-3 sentences maximum."""

        response = llm.invoke(summary_prompt)
        summary_content = response.content if hasattr(response, "content") else str(response)

        # Keep only the most recent messages (half of max_messages)
        keep_count = max(2, self.config.max_messages // 2)
        recent_messages = messages[-keep_count:]

        # Create new conversation with summary as first message + recent
        summary_message = AIMessage(
            content=f"[Conversation Summary]: {summary_content}"
        )

        self.conversations[conversation_id] = [summary_message] + recent_messages

        # Recalculate token count
        self._token_counts[conversation_id] = sum(
            self._estimate_tokens(m) for m in self.conversations[conversation_id]
        )

        logger.info(f"Summarized conversation {conversation_id}")

    def _format_messages_for_summary(self, messages: List[BaseMessage]) -> str:
        """Format messages for summarization prompt.

        Args:
            messages: List of messages to format

        Returns:
            Formatted string representation
        """
        formatted = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content if hasattr(msg, "content") else str(msg)
            formatted.append(f"{role}: {content[:500]}")  # Truncate long content

        return "\n".join(formatted)

    def _estimate_tokens(self, message: BaseMessage) -> int:
        """Estimate token count for a message.

        Uses a simple heuristic: ~4 characters per token for English.

        Args:
            message: Message to estimate

        Returns:
            Estimated token count
        """
        content = message.content if hasattr(message, "content") else ""
        return len(content) // 4 + 50  # Base overhead per message

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear all messages for a conversation.

        Args:
            conversation_id: Unique conversation identifier
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
            self._token_counts[conversation_id] = 0
            logger.info(f"Cleared conversation {conversation_id}")

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation entirely.

        Args:
            conversation_id: Unique conversation identifier
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            del self._token_counts[conversation_id]
            logger.info(f"Deleted conversation {conversation_id}")

    def list_conversations(self) -> List[str]:
        """List all conversation IDs.

        Returns:
            List of conversation IDs
        """
        return list(self.conversations.keys())

    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get statistics for a conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Dictionary with conversation statistics
        """
        if conversation_id not in self.conversations:
            return {
                "exists": False,
                "message_count": 0,
                "estimated_tokens": 0,
            }

        messages = self.conversations[conversation_id]
        return {
            "exists": True,
            "message_count": len(messages),
            "estimated_tokens": self._token_counts.get(conversation_id, 0),
            "message_types": {
                "human": sum(1 for m in messages if isinstance(m, HumanMessage)),
                "ai": sum(1 for m in messages if isinstance(m, AIMessage)),
            },
        }