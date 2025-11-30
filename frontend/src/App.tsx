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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
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
      <Sidebar 
        onNewChat={handleNewChat} 
        agentName={selectedAgentName}
        isMobileMenuOpen={isMobileMenuOpen}
        onMobileMenuClose={() => setIsMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0 md:ml-0">
        {/* Mobile Header with Burger Menu */}
        <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900 z-30">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Open menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="text-purple-400 text-sm font-medium leading-tight">iD4me</span>
              <span className="text-purple-600 text-xs font-semibold leading-tight">find</span>
            </div>
          </div>
          <div className="w-[44px]"></div> {/* Spacer for centering */}
        </div>
        <main className="flex-1 flex flex-col items-stretch overflow-hidden min-h-0">
          {selectedAgentId ? (
            <div className="flex-1 flex min-h-0 overflow-hidden px-2 md:px-4 py-3 md:py-6">
              <div className="w-full bg-zinc-950/80 border border-zinc-900/60 rounded-xl md:rounded-3xl overflow-hidden flex flex-col h-full">
                {(() => {
                  // Debug logging to verify prop passing
                  console.log('App - Passing to ChatMessageList:', {
                    selectedAgentName,
                    hasSelectedAgentName: !!selectedAgentName,
                    messagesCount: sortedMessages.length
                  });
                  return null;
                })()}
                {messages.length > 0 ? (
                  <>
                    <ChatMessageList messages={sortedMessages} isLoading={isLoading} agentName={selectedAgentName} />
                    <div className="flex-shrink-0 border-t border-zinc-800/60">
                      <ChatInput ref={chatInputRef} onSend={handleSend} disabled={isLoading} />
                    </div>
                  </>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center px-3 md:px-6 py-4 md:py-6">
                    <div className="w-[90%] flex flex-col items-center gap-2">
                      <ChatInput ref={chatInputRef} onSend={handleSend} disabled={isLoading} />
                      {showSuggestedQuestion && !isLoading && (
                        <div className="w-full flex flex-wrap justify-center gap-2">
                          <button
                            onClick={() => handleSend('Show me properties in my area')}
                            className="px-4 py-2.5 md:py-2 rounded-lg bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 text-xs md:text-sm font-medium transition-colors border border-zinc-700/50 hover:border-zinc-600 min-h-[44px]"
                          >
                            Show me properties in my area
                          </button>
                          <button
                            onClick={() => handleSend('Show me my listings')}
                            className="px-4 py-2.5 md:py-2 rounded-lg bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 text-xs md:text-sm font-medium transition-colors border border-zinc-700/50 hover:border-zinc-600 min-h-[44px]"
                          >
                            Show me my listings
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <AgentSelection onSelect={handleAgentSelect} />
          )}
        </main>

        {error ? (
          <div className="fixed bottom-4 md:bottom-6 left-4 md:left-auto md:right-6 right-4 bg-red-500/90 text-white px-4 py-2.5 rounded-md shadow-lg z-50 text-sm md:text-base max-w-[calc(100%-2rem)] md:max-w-none">
            {error}
          </div>
        ) : null}
      </div>
    </div>
  );
}

