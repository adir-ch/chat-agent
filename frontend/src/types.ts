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

export interface Area {
  name: string;
  postcode: string;
}

export interface AgentListItem {
  agent_id: string;
  first_name: string;
  last_name: string;
  agency: string;
  areas: Area[];
}

