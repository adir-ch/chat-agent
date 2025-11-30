import { FormEvent, useState, useRef, forwardRef, useImperativeHandle } from 'react';

interface Props {
  onSend: (value: string) => Promise<void>;
  disabled?: boolean;
}

export interface ChatInputHandle {
  focus: () => void;
}

export const ChatInput = forwardRef<ChatInputHandle, Props>(({ onSend, disabled }, ref) => {
  const [value, setValue] = useState('');
  const [pending, setPending] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => {
      inputRef.current?.focus();
    }
  }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || pending || disabled) return;

    setPending(true);
    try {
      await onSend(trimmed);
      setValue('');
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-[90%] mx-auto px-3 md:px-6 py-3 md:py-4"
    >
      <div className="bg-surface border border-zinc-800 rounded-xl md:rounded-2xl shadow-lg flex items-center py-2.5 md:py-3 px-3 md:px-4 gap-2 md:gap-3">
        <input
          ref={inputRef}
          className={`flex-1 bg-transparent placeholder:text-zinc-500 focus:outline-none text-sm md:text-base ${
            disabled || pending ? 'text-zinc-500' : 'text-zinc-100'
          }`}
          placeholder="Ask about your properties, clients, or market insights…"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          disabled={disabled || pending}
        />
        <button
          type="submit"
          disabled={disabled || pending}
          className="px-3 md:px-4 py-2 rounded-lg md:rounded-xl bg-accent text-zinc-950 font-medium disabled:opacity-60 disabled:cursor-not-allowed transition min-h-[44px] text-sm md:text-base"
        >
          Send
        </button>
      </div>
    </form>
  );
});

