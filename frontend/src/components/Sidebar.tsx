import { useState } from 'react';

interface Props {
  onNewChat?: () => void;
  logoPath?: string;
  agentName?: string | null;
  isMobileMenuOpen?: boolean;
  onMobileMenuClose?: () => void;
}

export function Sidebar({ onNewChat, logoPath, agentName, isMobileMenuOpen = false, onMobileMenuClose }: Props) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Close mobile menu when new chat is clicked
  const handleNewChat = () => {
    onNewChat?.();
    onMobileMenuClose?.();
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onMobileMenuClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        bg-zinc-900 border-r border-zinc-800 flex flex-col h-full transition-all duration-300
        fixed md:relative inset-y-0 left-0 z-50
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        ${isCollapsed ? 'w-16' : 'w-64'}
      `}>
      {/* Logo Section - hidden on mobile (shown in mobile header instead) */}
      <div className="hidden md:block p-4 border-b border-zinc-800 flex items-center justify-center min-h-[64px]">
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

      {/* Mobile close button - shown only on mobile when sidebar is open */}
      {!isCollapsed && (
        <div className="p-3 border-b border-zinc-800 md:hidden flex items-center justify-between">
          <div className="flex items-center gap-2">
            {logoPath ? (
              <img 
                src={logoPath} 
                alt="iD4me find logo" 
                className="h-8 w-auto object-contain"
              />
            ) : (
              <>
                <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="flex flex-col">
                  <span className="text-purple-400 text-sm font-medium leading-tight">iD4me</span>
                  <span className="text-purple-600 text-xs font-semibold leading-tight">find</span>
                </div>
              </>
            )}
          </div>
          <button
            onClick={onMobileMenuClose}
            className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Close menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* New Chat Button */}
      {!isCollapsed && (
        <div className="p-3 border-b border-zinc-800">
          <button
            onClick={handleNewChat}
            className="w-full px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-sm font-medium transition-colors flex items-center gap-2 min-h-[44px]"
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

      {/* Agent Name Section */}
      {!isCollapsed && agentName && (
        <div className="p-3 border-t border-zinc-800">
          <div className="flex items-center gap-2 px-2">
            <svg className="w-4 h-4 text-zinc-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span className="text-sm text-zinc-300 truncate font-medium">
              {agentName}
            </span>
          </div>
        </div>
      )}

      {/* Bottom Section: Agent Icon (when collapsed) and Collapse/Expand Button */}
      <div className="mt-auto border-t border-zinc-800">
        {/* Agent Icon when collapsed */}
        {isCollapsed && agentName && (
          <div className="p-3 border-b border-zinc-800 flex items-center justify-center">
            <svg className="w-5 h-5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        )}
        
        {/* Collapse/Expand Button - hidden on mobile */}
        <div className="p-3 hidden md:block">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="w-full px-3 py-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors flex items-center justify-center min-h-[44px]"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              // Right arrow ">" when closed
              <svg 
                className="w-5 h-5"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            ) : (
              // Left arrow "<" when open
              <svg 
                className="w-5 h-5"
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            )}
          </button>
        </div>
      </div>
      </div>
    </>
  );
}

