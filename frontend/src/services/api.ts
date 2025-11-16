import type { ChatRequest, ChatResponse } from '../types';

const API_BASE = '/api';

export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || 'Failed to contact LLM profile');
  }

  return res.json();
}

