import { memo } from 'react';
import type { ChatMessage } from '../types';

interface Props {
  messages: ChatMessage[];
  isLoading: boolean;
}

const roleStyles: Record<ChatMessage['role'], string> = {
  user: 'bg-surface/60 border border-zinc-800 ml-auto rounded-tl-xl rounded-tr-sm',
  assistant: 'bg-zinc-900 border border-zinc-800 mr-auto rounded-tr-xl rounded-tl-sm',
  system: 'bg-zinc-800 border border-zinc-700 mx-auto text-sm'
};

function ChatMessageItem({ message }: { message: ChatMessage }) {
  return (
    <div
      className={`max-w-[75%] px-4 py-3 rounded-b-xl shadow-sm ${roleStyles[message.role]}`}
    >
      <p className="whitespace-pre-wrap leading-relaxed text-zinc-100">
        {message.content}
      </p>
      <span className="mt-2 block text-[10px] uppercase tracking-wider text-zinc-500">
        {new Date(message.createdAt).toLocaleTimeString()}
      </span>
    </div>
  );
}

export const ChatMessageList = memo(({ messages, isLoading }: Props) => (
  <div className="flex-1 flex flex-col gap-4 overflow-y-auto px-6 py-6">
    {messages.map((msg) => (
      <ChatMessageItem key={msg.id} message={msg} />
    ))}
    {isLoading ? (
      <div className="mx-auto text-sm text-zinc-500 animate-pulse">Generating…</div>
    ) : null}
  </div>
));

