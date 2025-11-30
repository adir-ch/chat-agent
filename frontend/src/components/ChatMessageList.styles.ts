// Styles for ChatMessageList component

// User messages: Always in bubbles, max 85% width on mobile
export const userRoleStyles = 'bg-[indigo] border border-zinc-800 ml-auto rounded-tl-xl rounded-tr-sm';

// Assistant messages: Full-width on mobile (no bubble), bubble on desktop
export const assistantRoleStylesMobile = 'rounded-none shadow-none bg-transparent border-0'; // No bubble styling on mobile
export const assistantRoleStylesDesktop = 'md:bg-zinc-900 md:border md:border-zinc-800 md:mr-auto md:rounded-tr-xl md:rounded-tl-sm md:shadow-sm';

// System messages: Always in bubbles
export const systemRoleStyles = 'bg-zinc-800 border border-zinc-700 mx-auto text-sm';

// User message container: Bubble with max 85% width on mobile
export const userMessageContainerClasses = 'max-w-[85%] md:max-w-[75%] min-w-0 px-3 md:px-4 py-3 rounded-b-xl shadow-sm';

// Assistant message container: Full-width on mobile (breaks out of padding), bubble on desktop
export const assistantMessageContainerClassesMobile = 'w-full md:w-auto md:max-w-[75%] min-w-0 py-3 md:px-4 md:py-3 md:rounded-b-xl -mx-3 md:mx-0 px-3';

// Legacy container classes (for system messages)
export const messageContainerClasses = 'max-w-[95%] md:max-w-[75%] min-w-0 px-3 md:px-4 py-3 rounded-b-xl shadow-sm';

export const userMessageTextClasses = 'whitespace-pre-wrap leading-relaxed text-white break-words overflow-x-auto';

export const timestampClasses = 'mt-2 block text-[10px] tracking-wider text-zinc-500';

export const labelClasses = 'text-zinc-400';

export const proseClasses = 'prose prose-invert prose-sm max-w-none leading-relaxed min-w-0 overflow-x-auto';

// ReactMarkdown component styles
export const markdownStyles = {
  h1: 'text-xl font-bold mt-4 mb-2 text-zinc-100',
  h2: 'text-lg font-bold mt-3 mb-2 text-zinc-100',
  h3: 'text-base font-bold mt-3 mb-1 text-zinc-100',
  h4: 'text-sm font-bold mt-2 mb-1 text-zinc-100',
  h5: 'text-sm font-semibold mt-2 mb-1 text-zinc-100',
  h6: 'text-xs font-semibold mt-2 mb-1 text-zinc-100',
  p: 'mb-2 text-zinc-100 last:mb-0',
  ul: 'list-disc list-inside mb-2 space-y-1 text-zinc-100',
  ol: 'list-decimal list-inside mb-2 space-y-1 text-zinc-100',
  li: 'text-zinc-100',
  codeInline: 'bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-100 text-sm font-mono',
  code: 'text-zinc-100 text-sm font-mono',
  pre: 'bg-zinc-800 p-3 rounded-lg overflow-x-auto mb-2 text-zinc-100 whitespace-pre',
  a: 'text-blue-400 hover:text-blue-300 underline',
  blockquote: 'border-l-4 border-zinc-600 pl-4 italic text-zinc-300 mb-2',
  strong: 'font-bold text-zinc-100',
  em: 'italic text-zinc-100',
  hr: 'border-zinc-700 my-4',
  tableWrapper: 'overflow-x-auto mb-2',
  table: 'min-w-full border-collapse border border-zinc-700',
  thead: 'bg-zinc-800',
  tr: 'border-b border-zinc-700',
  th: 'border border-zinc-700 px-3 py-2 text-left font-semibold text-zinc-100',
  td: 'border border-zinc-700 px-3 py-2 text-zinc-100'
};

// Scroll container: Allow overflow-x on mobile for full-width assistant messages
export const scrollContainerClasses = 'flex-1 flex flex-col gap-3 md:gap-4 overflow-y-auto overflow-x-hidden md:overflow-x-hidden px-3 md:px-6 py-4 md:py-6';

export const loadingClasses = 'mx-auto text-xs md:text-sm text-zinc-500 animate-pulse';

export const bottomAnchorClasses = 'h-4 flex-shrink-0';

