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

export interface StreamingCallbacks {
  onChunk: (chunk: string) => void;
  onComplete: (tokenUsage?: { input_tokens: number; output_tokens: number; total_tokens: number }) => void;
  onError: (error: Error) => void;
}

export function sendChatMessageStream(
  payload: ChatRequest,
  callbacks: StreamingCallbacks
): () => void {
  /**
   * Send a chat message using Server-Sent Events (SSE) streaming via fetch.
   * Returns a cleanup function to abort the request.
   */
  const abortController = new AbortController();
  let accumulatedContent = '';

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: abortController.signal
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
        callbacks.onError(new Error(errorText || 'Stream request failed'));
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError(new Error('No response body'));
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // Remove 'data: ' prefix
              
              // Check if it's a JSON object (final message with token usage)
              if (data.startsWith('{')) {
                try {
                  const finalData = JSON.parse(data);
                  if (finalData.tokenUsage) {
                    callbacks.onComplete(finalData.tokenUsage);
                  } else if (finalData.error) {
                    callbacks.onError(new Error(finalData.error));
                  }
                  return;
                } catch (e) {
                  // Not JSON, treat as regular chunk
                }
              }
              
              // Regular token chunk - unescape newlines
              const unescapedChunk = data.replace(/\\n/g, '\n').replace(/\\r/g, '\r');
              accumulatedContent += unescapedChunk;
              callbacks.onChunk(unescapedChunk);
            }
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          // Request was aborted, don't call onError
          return;
        }
        callbacks.onError(error instanceof Error ? error : new Error('Unknown error'));
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        callbacks.onError(error instanceof Error ? error : new Error('Unknown error'));
      }
    });

  // Return cleanup function
  return () => {
    abortController.abort();
  };
}

