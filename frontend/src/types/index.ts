export interface QueryRequest {
  question: string;
  conversation_id?: string;
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
  sql: string;
  answer: string;
  data?: ChartDataPoint[];
  columns?: string[];
  chart_type?: string;
  intent?: string;
  attribution?: AttributionResult[];
  anomaly?: AnomalyResult[];
  conversation_id?: string;
  MOCK_MODE?: boolean;
}

export interface CampaignRequest {
  objective: string;
  audience_description: string;
  timing?: string;
  channels?: string[];
}

export interface AudienceInsight {
  label: string;
  value: string | number;
}

export interface AudiencePreviewResponse {
  estimated_count: number;
  insights: AudienceInsight[];
  rules: string[];
}

export interface Plan {
  id: string;
  name: string;
  description: string;
  estimated_reach: number;
  budget: string;
  recommended: boolean;
}

export interface PlansResponse {
  proposed_plans: Plan[];
}

export interface StrategyResponse {
  timing: string;
  channels: string[];
  content: string;
  message: string;
}

export interface Task {
  id: string;
  type: string;
  target: string;
  status: string;
  channel: string;
  content: string;
  scheduled_at?: string;
}

export interface TasksResponse {
  tasks: Task[];
  message: string;
}

export interface ConversationMessage {
  id: string;
  question: string;
  response?: QueryResponse;
  timestamp: number;
}