"""CDP (Customer Data Platform) client for audience building and segmentation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class CDPConfig:
    """Configuration for CDP client connection."""

    url: str
    api_key: str
    timeout: int = 30


class CDPClient(ABC):
    """Abstract base class for CDP client operations."""

    @abstractmethod
    def build_audience(self, hints: dict) -> dict:
        """Build an audience based on hints.

        Args:
            hints: Dictionary containing audience hints like demographics,
                   behaviors, interests, etc.

        Returns:
            audience_result dict with keys: id, name, rules, estimated_count, insights
        """
        pass

    @abstractmethod
    def get_audience(self, audience_id: str) -> dict:
        """Retrieve an audience by ID.

        Args:
            audience_id: The unique identifier of the audience.

        Returns:
            Audience data dictionary.
        """
        pass

    @abstractmethod
    def get_segments(self, audience_id: str) -> list[dict]:
        """Get detailed segments for an audience.

        Args:
            audience_id: The unique identifier of the audience.

        Returns:
            List of segment dictionaries with detailed segment information.
        """
        pass


class MockCDPClient(CDPClient):
    """Mock implementation of CDPClient for testing and development."""

    def __init__(self, config: Optional[CDPConfig] = None):
        """Initialize mock CDP client.

        Args:
            config: Optional CDP configuration.
        """
        self.config = config
        self._audiences = {}

    def build_audience(self, hints: dict) -> dict:
        """Build a mock audience based on hints.

        Uses keyword matching to generate appropriate segments and insights
        based on the provided hints.

        Args:
            hints: Dictionary containing audience hints.

        Returns:
            audience_result dict with id, name, rules, estimated_count, insights.
        """
        audience_id = str(uuid.uuid4())
        name = self._generate_name_from_hints(hints)
        rules = self._generate_rules_from_hints(hints)
        estimated_count = self._estimate_count_from_hints(hints)
        insights = self._generate_insights_from_hints(hints)

        audience_result = {
            "id": audience_id,
            "name": name,
            "rules": rules,
            "estimated_count": estimated_count,
            "insights": insights,
        }

        # Store for later retrieval
        self._audiences[audience_id] = audience_result

        return audience_result

    def get_audience(self, audience_id: str) -> dict:
        """Retrieve an audience by ID.

        Args:
            audience_id: The unique identifier of the audience.

        Returns:
            Audience data dictionary.
        """
        if audience_id in self._audiences:
            return self._audiences[audience_id]

        # Return a placeholder if not found
        return {
            "id": audience_id,
            "name": "Unknown Audience",
            "rules": [],
            "estimated_count": 0,
            "insights": "Audience not found.",
        }

    def get_segments(self, audience_id: str) -> list[dict]:
        """Get detailed segments for an audience.

        Args:
            audience_id: The unique identifier of the audience.

        Returns:
            List of segment dictionaries.
        """
        audience = self.get_audience(audience_id)

        # Generate segments based on audience name/insights
        segments = self._generate_segments_from_audience(audience)

        return segments

    def _generate_name_from_hints(self, hints: dict) -> str:
        """Generate audience name from hints."""
        keywords = []

        if "interests" in hints:
            interests = hints["interests"]
            if isinstance(interests, list):
                keywords.extend(interests[:2])
            else:
                keywords.append(str(interests))

        if "demographics" in hints:
            demo = hints["demographics"]
            if isinstance(demo, dict):
                if "age" in demo:
                    keywords.append(f"Age {demo['age']}")
                if "gender" in demo:
                    keywords.append(demo["gender"])

        if "behaviors" in hints:
            behaviors = hints["behaviors"]
            if isinstance(behaviors, list):
                keywords.extend(behaviors[:2])
            else:
                keywords.append(str(behaviors))

        if not keywords:
            return "General Audience"

        return f"{' '.join(keylines for keylines in keywords if keylines)}"

    def _generate_rules_from_hints(self, hints: dict) -> list[dict]:
        """Generate audience rules from hints."""
        rules = []

        if "demographics" in hints:
            demo = hints["demographics"]
            if isinstance(demo, dict):
                for key, value in demo.items():
                    rules.append({"field": key, "operator": "equals", "value": value})

        if "behaviors" in hints:
            behaviors = hints["behaviors"]
            if isinstance(behaviors, list):
                for behavior in behaviors:
                    rules.append(
                        {"field": "behavior", "operator": "contains", "value": behavior}
                    )
            else:
                rules.append(
                    {"field": "behavior", "operator": "contains", "value": behaviors}
                )

        if "interests" in hints:
            interests = hints["interests"]
            if isinstance(interests, list):
                for interest in interests:
                    rules.append(
                        {"field": "interest", "operator": "equals", "value": interest}
                    )
            else:
                rules.append(
                    {"field": "interest", "operator": "equals", "value": interests}
                )

        return rules

    def _estimate_count_from_hints(self, hints: dict) -> int:
        """Estimate audience count from hints."""
        base_count = 10000

        if "demographics" in hints:
            demo = hints["demographics"]
            if isinstance(demo, dict):
                if "age" in demo:
                    base_count *= 0.3
                if "gender" in demo:
                    base_count *= 0.5

        if "behaviors" in hints:
            behaviors = hints["behaviors"]
            if isinstance(behaviors, list):
                base_count *= 0.5 * len(behaviors)
            else:
                base_count *= 0.3

        if "interests" in hints:
            interests = hints["interests"]
            if isinstance(interests, list):
                base_count *= 0.4 * len(interests)
            else:
                base_count *= 0.2

        return max(int(base_count), 100)

    def _generate_insights_from_hints(self, hints: dict) -> str:
        """Generate audience insights from hints."""
        insights = []

        if "demographics" in hints:
            insights.append("Strong demographic presence in target segment.")

        if "behaviors" in hints:
            insights.append("High engagement behavior patterns detected.")

        if "interests" in hints:
            insights.append("Interest alignment with campaign objectives.")

        if not insights:
            return "General audience segment with broad characteristics."

        return " ".join(insights)

    def _generate_segments_from_audience(self, audience: dict) -> list[dict]:
        """Generate detailed segments from audience data."""
        segments = []

        name = audience.get("name", "")
        rules = audience.get("rules", [])

        # Create primary segment
        segments.append(
            {
                "id": str(uuid.uuid4()),
                "name": f"Primary - {name}",
                "type": "primary",
                "size": audience.get("estimated_count", 0),
                "rules": rules,
            }
        )

        # Create lookalike segment
        segments.append(
            {
                "id": str(uuid.uuid4()),
                "name": f"Lookalike - {name}",
                "type": "lookalike",
                "size": int(audience.get("estimated_count", 0) * 1.2),
                "similarity": 0.85,
            }
        )

        # Create high-value segment
        segments.append(
            {
                "id": str(uuid.uuid4()),
                "name": f"High-Value - {name}",
                "type": "high_value",
                "size": int(audience.get("estimated_count", 0) * 0.15),
                "avg_order_value": 150.0,
            }
        )

        return segments
