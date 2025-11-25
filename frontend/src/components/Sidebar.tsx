import { useState } from 'react';

interface Props {
  onNewChat?: () => void;
  logoPath?: string;
}

export function Sidebar({ onNewChat, logoPath }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className={`bg-zinc-900 border-r border-zinc-800 flex flex-col h-full transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Logo Section */}
      <div className="p-4 border-b border-zinc-800 flex items-center justify-center min-h-[64px]">
        {!isCollapsed ? (
          <div className="flex items-center gap-2">
            {logoPath ? (
              <img 
                src={logoPath} 
                alt="iD4me find logo" 
                className="h-8 w-auto object-contain"
              />
            ) : (
              <>
                {/* Logo - purple checkmark circle icon */}
                <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                {/* Logo text */}
                <div className="flex flex-col">
                  <span className="text-purple-400 text-sm font-medium leading-tight">iD4me</span>
                  <span className="text-purple-600 text-xs font-semibold leading-tight">find</span>
                </div>
              </>
            )}
          </div>
        ) : (
          logoPath ? (
            <img 
              src={logoPath} 
              alt="iD4me find logo" 
              className="h-8 w-auto object-contain"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          )
        )}
      </div>

      {/* New Chat Button */}
      {!isCollapsed && (
        <div className="p-3 border-b border-zinc-800">
          <button
            onClick={onNewChat}
            className="w-full px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-sm font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>
      )}

      {/* Chat History Section - placeholder for future implementation */}
      {!isCollapsed && (
        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs text-zinc-500 uppercase tracking-wider px-3 py-2">
            Recent
          </div>
          {/* Chat history items would go here */}
        </div>
      )}

      {/* Collapse/Expand Button */}
      <div className="p-3 border-t border-zinc-800">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full px-3 py-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors flex items-center justify-center"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <svg 
            className={`w-5 h-5 transition-transform ${isCollapsed ? '' : 'rotate-180'}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

