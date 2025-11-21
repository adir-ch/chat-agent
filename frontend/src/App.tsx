import { useCallback, useMemo, useState, useRef } from 'react';
import { ChatInput, type ChatInputHandle } from './components/ChatInput';
import { ChatMessageList } from './components/ChatMessageList';
import { AgentSelection } from './components/AgentSelection';
import { sendChatMessage } from './services/api';
import type { ChatMessage } from './types';

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const chatInputRef = useRef<ChatInputHandle>(null);

  const sortedMessages = useMemo(
    () => [...messages].sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()),
    [messages]
  );

  const handleAgentSelect = useCallback((agentId: string, agentName: string) => {
    setSelectedAgentId(agentId);
    setSelectedAgentName(agentName);
    setMessages([]);
    setError(null);
  }, []);

  const handleSend = useCallback(
    async (content: string) => {
      if (!selectedAgentId) {
        setError('No agent selected');
        return;
      }

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
          agentId: selectedAgentId,
          message: content
        });
        // Include tokenUsage in the message if available
        const assistantMessage: ChatMessage = {
          ...response.message,
          tokenUsage: response.tokenUsage
        };
        setMessages((prev) => [...prev, assistantMessage]);
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
    [selectedAgentId]
  );

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col text-zinc-100">
      <header className="px-6 pt-8 pb-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              {selectedAgentName ? selectedAgentName : 'Agent Assist'}
            </h1>
            <p className="text-sm text-zinc-500">
              {selectedAgentName
                ? 'Personalised insights powered by your local data.'
                : 'Personalised insights powered by your local data.'}
            </p>
          </div>
          <span className="text-xs text-zinc-500 uppercase tracking-widest">BETA</span>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-stretch">
        {selectedAgentId ? (
          <div className="flex-1 flex justify-center">
            <div className="w-full max-w-3xl bg-zinc-950/80 border border-zinc-900/60 rounded-3xl overflow-hidden flex flex-col">
              {(() => {
                // Debug logging to verify prop passing
                console.log('App - Passing to ChatMessageList:', {
                  selectedAgentName,
                  hasSelectedAgentName: !!selectedAgentName,
                  messagesCount: sortedMessages.length
                });
                return null;
              })()}
              <ChatMessageList messages={sortedMessages} isLoading={isLoading} agentName={selectedAgentName} />
              <ChatInput ref={chatInputRef} onSend={handleSend} disabled={isLoading} />
            </div>
          </div>
        ) : (
          <AgentSelection onSelect={handleAgentSelect} />
        )}
      </main>

      {error ? (
        <div className="fixed bottom-6 right-6 bg-red-500/90 text-white px-4 py-2 rounded-md shadow-lg">
          {error}
        </div>
      ) : null}
    </div>
  );
}

