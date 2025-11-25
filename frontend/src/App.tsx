import { useCallback, useMemo, useState, useRef } from 'react';
import { ChatInput, type ChatInputHandle } from './components/ChatInput';
import { ChatMessageList } from './components/ChatMessageList';
import { AgentSelection } from './components/AgentSelection';
import { Sidebar } from './components/Sidebar';
import { sendChatMessage } from './services/api';
import type { ChatMessage } from './types';

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedAgentName, setSelectedAgentName] = useState<string | null>(null);
  const [showSuggestedQuestion, setShowSuggestedQuestion] = useState(false);
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
    setShowSuggestedQuestion(true);
  }, []);

  const handleNewChat = useCallback(() => {
    // Reset all state to go back to agent selection
    setSelectedAgentId(null);
    setSelectedAgentName(null);
    setMessages([]);
    setError(null);
    setLoading(false);
    setShowSuggestedQuestion(false);
    // Focus will be handled by AgentSelection component
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
      // Hide suggested question after sending any message
      setShowSuggestedQuestion(false);

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
    <div className="h-screen bg-zinc-950 flex text-zinc-100 overflow-hidden">
      {/* Sidebar */}
      <Sidebar onNewChat={handleNewChat} agentName={selectedAgentName} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <main className="flex-1 flex flex-col items-stretch overflow-hidden min-h-0">
          {selectedAgentId ? (
            <div className="flex-1 flex min-h-0 overflow-hidden px-4 py-6">
              <div className="w-full bg-zinc-950/80 border border-zinc-900/60 rounded-3xl overflow-hidden flex flex-col h-full">
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
                <div className="flex-shrink-0 border-t border-zinc-800/60 flex flex-col">
                  {showSuggestedQuestion && messages.length === 0 && !isLoading && (
                    <div className="px-6 pt-3 pb-2 flex justify-center">
                      <button
                        onClick={() => handleSend('Show me properties in my area')}
                        className="px-4 py-2 rounded-lg bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 text-sm font-medium transition-colors border border-zinc-700/50 hover:border-zinc-600"
                      >
                        Show me properties in my area
                      </button>
                    </div>
                  )}
                  <ChatInput ref={chatInputRef} onSend={handleSend} disabled={isLoading} />
                </div>
              </div>
            </div>
          ) : (
            <AgentSelection onSelect={handleAgentSelect} />
          )}
        </main>

        {error ? (
          <div className="fixed bottom-6 right-6 bg-red-500/90 text-white px-4 py-2 rounded-md shadow-lg z-50">
            {error}
          </div>
        ) : null}
      </div>
    </div>
  );
}

