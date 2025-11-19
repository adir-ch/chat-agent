import type { ChatRequest, ChatResponse, AgentListItem } from '../types';

const API_BASE = import.meta.env.VITE_AGENT_URL || 'http://localhost:8070';
const PROFILE_BASE = import.meta.env.VITE_PROFILE_URL || 'http://localhost:8080';

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to contact agent service');
  }

  return res.json();
}

export async function getAgents(): Promise<AgentListItem[]> {
  const res = await fetch(`${PROFILE_BASE}/api/agents`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' }
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to fetch agents');
  }

  return res.json();
}

