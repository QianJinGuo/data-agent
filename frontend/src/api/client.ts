import axios from 'axios';
import type {
  QueryResponse,
  CampaignResponse,
  StrategyResponse,
  Task,
} from '../types';

const API_BASE = 'http://localhost:8000'; // override via VITE_API_BASE env if needed

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function queryNL2SQL(
  question: string,
  conversationId?: string
): Promise<QueryResponse> {
  const response = await client.post<QueryResponse>('/query', {
    question,
    conversation_id: conversationId,
  });
  return response.data;
}

export async function createCampaign(
  objective: string,
  audienceDescription: string,
  timing?: Record<string, unknown>,
  channels?: string[]
): Promise<CampaignResponse> {
  const response = await client.post<CampaignResponse>('/marketing/campaigns', {
    objective,
    audience_description: audienceDescription,
    timing: timing ?? {},
    channels: channels ?? [],
  });
  return response.data;
}

export async function applyPlan(
  planId: string,
  channels: string[],
  content?: Record<string, unknown>
): Promise<StrategyResponse> {
  const response = await client.post<StrategyResponse>(
    `/marketing/plans/${planId}/apply`,
    { channels, content: content ?? {} }
  );
  return response.data;
}

export async function listTasks(): Promise<{ tasks: Task[]; total: number }> {
  const response = await client.get<{ tasks: Task[]; total: number }>('/marketing/tasks');
  return response.data;
}

export default client;