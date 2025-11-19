import { useCallback, useMemo, useState, useRef } from 'react';
import { ChatInput, type ChatInputHandle } from './components/ChatInput';
import { ChatMessageList } from './components/ChatMessageList';
import { sendChatMessage } from './services/api';
import type { ChatMessage } from './types';

const DEFAULT_AGENT_ID = 'agent-123';

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(false);
  const chatInputRef = useRef<ChatInputHandle>(null);

  const sortedMessages = useMemo(
    () => [...messages].sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()),
    [messages]
  );

  const handleSend = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        createdAt: new Date().toISOString()
      };

      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      try {
        const response = await sendChatMessage({
          agentId: DEFAULT_AGENT_ID,
          message: content
        });
        setMessages((prev) => [...prev, response.message]);
        // Focus input after receiving response
        setTimeout(() => {
          chatInputRef.current?.focus();
        }, 100);
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        // Focus input even on error
        setTimeout(() => {
          chatInputRef.current?.focus();
        }, 100);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col text-zinc-100">
      <header className="px-6 pt-8 pb-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Agent Assist</h1>
            <p className="text-sm text-zinc-500">Personalised insights powered by your local data.</p>
          </div>
          <span className="text-xs text-zinc-500 uppercase tracking-widest">BETA</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-stretch">
        <div className="flex-1 flex justify-center">
          <div className="w-full max-w-3xl bg-zinc-950/80 border border-zinc-900/60 rounded-3xl overflow-hidden flex flex-col">
            <ChatMessageList messages={sortedMessages} isLoading={isLoading} />
            <ChatInput ref={chatInputRef} onSend={handleSend} disabled={isLoading} />
          </div>
        </div>
      </main>

      {error ? (
        <div className="fixed bottom-6 right-6 bg-red-500/90 text-white px-4 py-2 rounded-md shadow-lg">
          {error}
        </div>
      ) : null}
    </div>
  );
}

