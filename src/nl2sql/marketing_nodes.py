"""Graph nodes for the Marketing Strategy LangGraph pipeline."""
import json
import uuid
from datetime import datetime


def parse_objective(state: dict, llm) -> dict:
    """Parse campaign description into campaign objective and audience hints."""
    last_msg = state["messages"][-1].content if state["messages"] else ""

    prompt = f"""Parse the following campaign description to extract:
1. campaign_objective: the main marketing goal (e.g., awareness, conversion, retention)
2. audience_hints: key characteristics of target audience mentioned or implied

Campaign description: {last_msg}

Return a JSON object with:
- "campaign_objective": string describing the main objective
- "audience_hints": object with hints about target audience (age, location, interests, behavior, etc.)

Return JSON only, no markdown."""
    response = llm.invoke(prompt)
    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"campaign_objective": "unknown", "audience_hints": {}}

    return {
        "campaign_objective": parsed.get("campaign_objective", ""),
        "audience_insights": json.dumps({"audience_hints": parsed.get("audience_hints", {})}, ensure_ascii=False),
    }


def audience_build(state: dict, llm, cdp_client=None) -> dict:
    """Build target audience using CDP based on audience hints."""
    campaign_objective = state.get("campaign_objective", "")
    audience_hints_str = state.get("audience_insights", "{}")

    try:
        audience_hints = json.loads(audience_hints_str).get("audience_hints", {})
    except Exception:
        audience_hints = {}

    # Use CDP client if available to build real audience
    if cdp_client:
        try:
            audience_result = cdp_client.build_audience(
                objective=campaign_objective,
                hints=audience_hints,
            )
            target_audience = audience_result.get("audience", {})
            audience_insights = audience_result.get("insights", "")
        except Exception as e:
            target_audience = {"error": str(e)}
            audience_insights = ""
    else:
        # Mock audience building
        target_audience = {
            "id": str(uuid.uuid4()),
            "name": f"Auto-generated audience for {campaign_objective}",
            "rules": [
                {"field": "age_range", "operator": "between", "value": [25, 45]},
                {"field": "engagement_level", "operator": "gte", "value": 3},
            ],
            "estimated_count": 150000,
        }
        audience_insights = f"Target audience auto-generated for objective: {campaign_objective}. Estimated reach: 150,000 users."

    return {
        "target_audience": target_audience,
        "audience_insights": audience_insights,
    }


def plan_generate(state: dict, llm) -> dict:
    """Generate N marketing plan proposals split by 人群/渠道/内容 dimensions."""
    campaign_objective = state.get("campaign_objective", "")
    target_audience = state.get("target_audience", {})
    audience_insights = state.get("audience_insights", "")

    audience_name = target_audience.get("name", "general users") if isinstance(target_audience, dict) else "general users"

    prompt = f"""Generate 3 marketing plan proposals for the following campaign.

Campaign Objective: {campaign_objective}
Target Audience: {audience_name}
Audience Insights: {audience_insights}

Generate plans across these dimensions:
1. 人群 (Audience): plans targeting different audience segments
2. 渠道 (Channel): plans using different marketing channels
3. 内容 (Content): plans with different content strategies

Return a JSON object with:
- "plans": array of plan objects, each with:
  - "id": unique plan id
  - "name": plan name
  - "dimension": "人群" | "渠道" | "内容"
  - "description": detailed plan description
  - "estimated_effect": expected outcome
  - "受众用户": target user description

Return JSON only, no markdown."""
    response = llm.invoke(prompt)
    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"plans": []}

    plans = parsed.get("plans", [])
    # Ensure at least one plan exists
    if not plans:
        plans = [
            {
                "id": str(uuid.uuid4()),
                "name": "Default Plan",
                "dimension": "综合",
                "description": "Default marketing plan",
                "estimated_effect": "中等",
                "受众用户": audience_name,
            }
        ]

    return {"proposed_plans": plans}


def strategy_generate(state: dict, llm) -> dict:
    """Generate strategy from selected plan: timing, channel priority, content variants."""
    proposed_plans = state.get("proposed_plans", [])
    selected_plan = state.get("selected_plan", {})

    # Use selected plan or pick the first one
    if not selected_plan and proposed_plans:
        selected_plan = proposed_plans[0]
    elif not selected_plan:
        return {"generated_strategy": None, "error": "No plan selected"}

    plan_name = selected_plan.get("name", "Unknown Plan")
    plan_dimension = selected_plan.get("dimension", "")
    plan_description = selected_plan.get("description", "")

    prompt = f"""Generate a detailed marketing strategy based on the selected plan.

Selected Plan:
- Name: {plan_name}
- Dimension: {plan_dimension}
- Description: {plan_description}

Generate a strategy with:
1. timing_design: array of timing configurations with start_date, end_date, frequency
2. channel_priority: object ranking channels by priority (e.g., {{"social": 1, "email": 2, "push": 3}})
3. content_variants: array of content variations with theme, tone, key_messages

Return a JSON object with:
- "id": strategy id
- "timing_design": array of timing objects
- "channel_priority": dict of channel priorities
- "content_variants": array of content variant objects

Return JSON only, no markdown."""
    response = llm.invoke(prompt)
    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"id": str(uuid.uuid4()), "timing_design": [], "channel_priority": {}, "content_variants": []}

    parsed["id"] = parsed.get("id", str(uuid.uuid4()))
    return {"generated_strategy": parsed}


def task_config(state: dict) -> dict:
    """Convert strategy into outreach tasks with audience/trigger/channel configuration."""
    generated_strategy = state.get("generated_strategy")
    target_audience = state.get("target_audience", {})
    campaign_objective = state.get("campaign_objective", "")

    if not generated_strategy:
        return {
            "outreach_tasks": [],
            "final_answer": "No strategy generated. Cannot create outreach tasks.",
            "error": "Missing strategy",
        }

    audience_id = target_audience.get("id", "unknown") if isinstance(target_audience, dict) else "unknown"
    timing_design = generated_strategy.get("timing_design", [])
    channel_priority = generated_strategy.get("channel_priority", {})
    content_variants = generated_strategy.get("content_variants", [])

    # Generate outreach tasks for each timing + channel combination
    tasks = []
    task_id = 1

    for timing in timing_design:
        for channel, priority in channel_priority.items():
            content = content_variants[0] if content_variants else {}
            tasks.append(
                {
                    "id": f"task_{task_id}",
                    "campaign_id": f"campaign_{uuid.uuid4().hex[:8]}",
                    "audience_id": audience_id,
                    "trigger_condition": f"at {timing.get('start_date', 'TBD')}",
                    "channel": channel,
                    "template_id": f"template_{channel}_{task_id}",
                    "status": "pending",
                }
            )
            task_id += 1

    # Build final answer
    final_answer = f"""Marketing campaign configured successfully.

Objective: {campaign_objective}
Target Audience: {target_audience.get('name', 'Unknown') if isinstance(target_audience, dict) else 'Unknown'}
Estimated Audience Size: {target_audience.get('estimated_count', 'N/A') if isinstance(target_audience, dict) else 'N/A'}

Generated {len(tasks)} outreach task(s) across {len(channel_priority)} channel(s).
"""

    return {
        "outreach_tasks": tasks,
        "final_answer": final_answer,
    }