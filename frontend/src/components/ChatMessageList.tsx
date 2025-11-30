import { memo, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage } from '../types';
import {
  roleStyles,
  messageContainerClasses,
  userMessageTextClasses,
  timestampClasses,
  labelClasses,
  proseClasses,
  markdownStyles,
  scrollContainerClasses,
  loadingClasses,
  bottomAnchorClasses
} from './ChatMessageList.styles';

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
  agentName?: string | null;
}

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
      className={`${messageContainerClasses} ${roleStyles[message.role]}`}
    >
      {message.role === 'assistant' ? (
        <div className={proseClasses}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // Headings
              h1: ({ node, ...props }) => <h1 className={markdownStyles.h1} {...props} />,
              h2: ({ node, ...props }) => <h2 className={markdownStyles.h2} {...props} />,
              h3: ({ node, ...props }) => <h3 className={markdownStyles.h3} {...props} />,
              h4: ({ node, ...props }) => <h4 className={markdownStyles.h4} {...props} />,
              h5: ({ node, ...props }) => <h5 className={markdownStyles.h5} {...props} />,
              h6: ({ node, ...props }) => <h6 className={markdownStyles.h6} {...props} />,
              // Paragraphs
              p: ({ node, ...props }) => <p className={markdownStyles.p} {...props} />,
              // Lists
              ul: ({ node, ...props }) => <ul className={markdownStyles.ul} {...props} />,
              ol: ({ node, ...props }) => <ol className={markdownStyles.ol} {...props} />,
              li: ({ node, ...props }) => <li className={markdownStyles.li} {...props} />,
              // Code blocks
              code: ({ node, className, children, ...props }: any) => {
                const isInline = !className;
                return isInline ? (
                  <code className={markdownStyles.codeInline} {...props}>
                    {children}
                  </code>
                ) : (
                  <code className={markdownStyles.code} {...props}>
                    {children}
                  </code>
                );
              },
              pre: ({ node, ...props }) => <pre className={markdownStyles.pre} {...props} />,
              // Links
              a: ({ node, ...props }) => <a className={markdownStyles.a} {...props} />,
              // Blockquotes
              blockquote: ({ node, ...props }) => (
                <blockquote className={markdownStyles.blockquote} {...props} />
              ),
              // Strong and emphasis
              strong: ({ node, ...props }) => <strong className={markdownStyles.strong} {...props} />,
              em: ({ node, ...props }) => <em className={markdownStyles.em} {...props} />,
              // Horizontal rule
              hr: ({ node, ...props }) => <hr className={markdownStyles.hr} {...props} />,
              // Tables (from remark-gfm)
              table: ({ node, ...props }) => (
                <div className={markdownStyles.tableWrapper}>
                  <table className={markdownStyles.table} {...props} />
                </div>
              ),
              thead: ({ node, ...props }) => <thead className={markdownStyles.thead} {...props} />,
              tbody: ({ node, ...props }) => <tbody {...props} />,
              tr: ({ node, ...props }) => <tr className={markdownStyles.tr} {...props} />,
              th: ({ node, ...props }) => <th className={markdownStyles.th} {...props} />,
              td: ({ node, ...props }) => <td className={markdownStyles.td} {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      ) : (
        <p className={userMessageTextClasses}>
          {message.content}
        </p>
      )}
      <span className={timestampClasses}>
        {label ? (
          <>
            <span>{timeString}</span>
            <span className="mx-1.5">•</span>
            <span className={labelClasses}>{label}</span>
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
      className={scrollContainerClasses}
      style={{ scrollBehavior: 'smooth' }}
    >
      {messages.map((msg) => (
        <ChatMessageItem key={msg.id} message={msg} agentName={agentName} />
      ))}
      {isLoading ? (
        <div className={loadingClasses}>Thinking…</div>
      ) : null}
      <div ref={bottomAnchorRef} className={bottomAnchorClasses} />
    </div>
  );
});

