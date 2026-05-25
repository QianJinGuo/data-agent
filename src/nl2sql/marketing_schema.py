"""Data models for Marketing Strategy pipeline."""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AudienceSegment(BaseModel):
    """Target audience segment from CDP."""

    id: str
    name: str
    rules: list[dict] = Field(default_factory=list)
    estimated_count: int = 0
    insights: Optional[str] = None
    created_at: Optional[datetime] = None


class MarketingPlan(BaseModel):
    """Marketing plan proposal."""

    id: str
    name: str
    dimension: str  # 人群/渠道/内容
    description: str
    estimated_effect: str
    受众用户: Optional[str] = None  # target users


class Strategy(BaseModel):
    """Generated marketing strategy."""

    id: str
    timing_design: list[dict] = Field(default_factory=list)
    channel_priority: dict = Field(default_factory=dict)
    content_variants: list[dict] = Field(default_factory=list)


class OutreachTask(BaseModel):
    """Outreach task configuration."""

    id: str
    campaign_id: str
    audience_id: str
    trigger_condition: str
    channel: str
    template_id: str
    status: str = "pending"


class MarketingCampaign(BaseModel):
    """Marketing campaign."""

    id: str
    name: str
    objective: str
    audience_id: str
    timing: dict = Field(default_factory=dict)
    channels: list[str] = Field(default_factory=list)
    status: str = "draft"
    created_at: Optional[datetime] = None