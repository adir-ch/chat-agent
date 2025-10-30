export type Role = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
}

export interface ChatRequest {
  agentId: string;
  message: string;
}

export interface ChatResponse {
  message: ChatMessage;
  contextSummary?: string;
}

