import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  CampaignRequest,
  AudiencePreviewResponse,
  PlansResponse,
  StrategyResponse,
  Task,
  TasksResponse,
} from '../types';

const client = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function queryNL2SQL(
  question: string,
  conversationId?: string
): Promise<QueryResponse> {
  const request: QueryRequest = { question };
  if (conversationId) {
    request.conversation_id = conversationId;
  }
  const response = await client.post<QueryResponse>('/api/nl2sql', request);
  return response.data;
}

export async function createCampaign(
  objective: string,
  audienceDescription: string,
  timing?: string,
  channels?: string[]
): Promise<AudiencePreviewResponse> {
  const request: CampaignRequest = {
    objective,
    audience_description: audienceDescription,
  };
  if (timing) request.timing = timing;
  if (channels) request.channels = channels;
  const response = await client.post<AudiencePreviewResponse>('/api/campaign/create', request);
  return response.data;
}

export async function getPlans(
  objective: string,
  audienceDescription: string,
  channels?: string[]
): Promise<PlansResponse> {
  const params: Record<string, string> = {
    objective,
    audience_description: audienceDescription,
  };
  if (channels && channels.length > 0) {
    params.channels = channels.join(',');
  }
  const response = await client.get<PlansResponse>('/api/campaign/plans', { params });
  return response.data;
}

export async function applyPlan(
  planId: string,
  channels: string[],
  content?: string
): Promise<TasksResponse> {
  const response = await client.post<TasksResponse>('/api/campaign/apply', {
    plan_id: planId,
    channels,
    content,
  });
  return response.data;
}

export async function listTasks(): Promise<TasksResponse> {
  const response = await client.get<TasksResponse>('/api/campaign/tasks');
  return response.data;
}

export default client;