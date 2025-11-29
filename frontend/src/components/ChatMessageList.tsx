import { memo, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types';

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
  agentName?: string | null;
}

const roleStyles: Record<ChatMessage['role'], string> = {
  user: 'bg-surface/60 border border-zinc-800 ml-auto rounded-tl-xl rounded-tr-sm',
  assistant: 'bg-zinc-900 border border-zinc-800 mr-auto rounded-tr-xl rounded-tl-sm',
  system: 'bg-zinc-800 border border-zinc-700 mx-auto text-sm'
};

function ChatMessageItem({ message, agentName }: { message: ChatMessage; agentName?: string | null }) {
  const timeString = new Date(message.createdAt).toLocaleTimeString();
  
  // Show label based on message role
  let label: string | null = null;
  if (message.role === 'assistant') {
    label = 'Assistant';
  } else if (message.role === 'user') {
    label = agentName || 'User';
  }
  
  // Format token counts for assistant messages
  const tokenInfo = message.role === 'assistant' && message.tokenUsage
    ? `, (tokens: in=${message.tokenUsage.input_tokens}, out=${message.tokenUsage.output_tokens}, total=${message.tokenUsage.total_tokens})`
    : '';
  
  return (
    <div
      className={`max-w-[95%] md:max-w-[75%] min-w-0 px-3 md:px-4 py-3 rounded-b-xl shadow-sm ${roleStyles[message.role]}`}
    >
      {message.role === 'assistant' ? (
        <div className="prose prose-invert prose-sm max-w-none leading-relaxed min-w-0 overflow-x-auto">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Headings
              h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-4 mb-2 text-zinc-100" {...props} />,
              h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-3 mb-2 text-zinc-100" {...props} />,
              h3: ({ node, ...props }) => <h3 className="text-base font-bold mt-3 mb-1 text-zinc-100" {...props} />,
              h4: ({ node, ...props }) => <h4 className="text-sm font-bold mt-2 mb-1 text-zinc-100" {...props} />,
              h5: ({ node, ...props }) => <h5 className="text-sm font-semibold mt-2 mb-1 text-zinc-100" {...props} />,
              h6: ({ node, ...props }) => <h6 className="text-xs font-semibold mt-2 mb-1 text-zinc-100" {...props} />,
              // Paragraphs
              p: ({ node, ...props }) => <p className="mb-2 text-zinc-100 last:mb-0" {...props} />,
              // Lists
              ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1 text-zinc-100" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-zinc-100" {...props} />,
              li: ({ node, ...props }) => <li className="text-zinc-100" {...props} />,
              // Code blocks
              code: ({ node, className, children, ...props }: any) => {
                const isInline = !className;
                return isInline ? (
                  <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-100 text-sm font-mono" {...props}>
                    {children}
                  </code>
                ) : (
                  <code className="text-zinc-100 text-sm font-mono" {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({ node, ...props }) => <pre className="bg-zinc-800 p-3 rounded-lg overflow-x-auto mb-2 text-zinc-100 whitespace-pre" {...props} />,
              // Links
              a: ({ node, ...props }) => <a className="text-blue-400 hover:text-blue-300 underline" {...props} />,
              // Blockquotes
              blockquote: ({ node, ...props }) => (
                <blockquote className="border-l-4 border-zinc-600 pl-4 italic text-zinc-300 mb-2" {...props} />
              ),
              // Strong and emphasis
              strong: ({ node, ...props }) => <strong className="font-bold text-zinc-100" {...props} />,
              em: ({ node, ...props }) => <em className="italic text-zinc-100" {...props} />,
              // Horizontal rule
              hr: ({ node, ...props }) => <hr className="border-zinc-700 my-4" {...props} />,
              // Tables (from remark-gfm)
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto mb-2">
                  <table className="min-w-full border-collapse border border-zinc-700" {...props} />
                </div>
              ),
              thead: ({ node, ...props }) => <thead className="bg-zinc-800" {...props} />,
              tbody: ({ node, ...props }) => <tbody {...props} />,
              tr: ({ node, ...props }) => <tr className="border-b border-zinc-700" {...props} />,
              th: ({ node, ...props }) => <th className="border border-zinc-700 px-3 py-2 text-left font-semibold text-zinc-100" {...props} />,
              td: ({ node, ...props }) => <td className="border border-zinc-700 px-3 py-2 text-zinc-100" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      ) : (
        <p className="whitespace-pre-wrap leading-relaxed text-zinc-100 break-words overflow-x-auto">
          {message.content}
        </p>
      )}
      <span className="mt-2 block text-[10px] tracking-wider text-zinc-500">
        {label ? (
          <>
            <span>{timeString}</span>
            <span className="mx-1.5">•</span>
            <span className="text-zinc-400">{label}</span>
            {tokenInfo && <span>{tokenInfo}</span>}
          </>
        ) : (
          <>
            {timeString}
            {tokenInfo && <span>{tokenInfo}</span>}
          </>
        )}
      </span>
    </div>
  );
}

export const ChatMessageList = memo(({ messages, isLoading, agentName }: Props) => {
  // Debug logging to verify prop passing
  console.log('ChatMessageList - Props:', {
    agentName,
    hasAgentName: !!agentName,
    messagesCount: messages.length,
    assistantMessages: messages.filter(m => m.role === 'assistant').length
  });
  
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const bottomAnchorRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    // Use requestAnimationFrame for smoother scrolling
    requestAnimationFrame(() => {
      if (scrollContainerRef.current) {
        const container = scrollContainerRef.current;
        // Scroll to the absolute bottom of the container
        // The input box is outside this container, so scrolling here won't affect it
        container.scrollTop = container.scrollHeight;
      }
    });
  }, []);

  // Scroll to bottom when messages change or loading state changes
  useEffect(() => {
    if (messages.length > 0 || isLoading) {
      // Use setTimeout to ensure DOM has updated, then use requestAnimationFrame for smooth scroll
      const timeoutId = setTimeout(() => {
        scrollToBottom();
      }, 150);
      return () => clearTimeout(timeoutId);
    }
  }, [messages.length, isLoading, scrollToBottom]);

  return (
    <div 
      ref={scrollContainerRef}
      className="flex-1 flex flex-col gap-3 md:gap-4 overflow-y-auto px-3 md:px-6 py-4 md:py-6"
      style={{ scrollBehavior: 'smooth' }}
    >
      {messages.map((msg) => (
        <ChatMessageItem key={msg.id} message={msg} agentName={agentName} />
      ))}
      {isLoading ? (
        <div className="mx-auto text-xs md:text-sm text-zinc-500 animate-pulse">Thinking…</div>
      ) : null}
      <div ref={bottomAnchorRef} className="h-4 flex-shrink-0" />
    </div>
  );
});

