export interface QueryRequest {
  question: string;
  conversation_id?: string;
  dataset_ids?: string[];
}

export interface AttributionResult {
  field: string;
  value: string;
  confidence: number;
}

export interface AnomalyResult {
  field: string;
  expected: string;
  actual: string;
  severity: string;
}

export interface ChartDataPoint {
  [key: string]: string | number;
}

export interface QueryResponse {
  final_answer: string;
  sql: string;
  query_result?: { rows: ChartDataPoint[]; columns: string[] };
  chart_type: string;
  intent: string;
}

export interface CampaignRequest {
  objective: string;
  audience_description: string;
  timing?: Record<string, unknown>;
  channels?: string[];
}

export interface AudienceResult {
  id: string;
  name: string;
  rules: Record<string, unknown>[];
  estimated_count: number;
  insights: string;
}

export interface Plan {
  id: string;
  name: string;
  dimension: string;
  description: string;
  estimated_effect: string;
  受众用户?: string;
}

export interface CampaignResponse {
  campaign_id: string;
  audience_result?: AudienceResult;
  proposed_plans: Plan[];
}

export interface StrategyResponse {
  strategy_id: string;
  timing_design: { phase: string; timing: string; action: string }[];
  content_variants: { variant: string; channel: string; template: string }[];
}

export interface Task {
  id: string;
  campaign_id: string;
  audience_id: string;
  trigger_condition: string;
  channel: string;
  template_id: string;
  status: string;
}

export interface TasksResponse {
  tasks: Task[];
  total: number;
}

export interface ConversationMessage {
  id: string;
  question: string;
  response?: QueryResponse;
  timestamp: number;
}