import { Bell, MessageSquare, Calendar, ChevronDown, Search, User } from 'lucide-react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  onOpenChat?: () => void;
  showSearch?: boolean;
}

export function Header({ title, subtitle, onOpenChat, showSearch = true }: HeaderProps) {
  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <header className="bg-white border-b border-neutral-100 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side - Title & Date */}
        <div>
          {title && (
            <h1 className="text-heading-lg text-neutral-950">{title}</h1>
          )}
          {subtitle ? (
            <p className="text-body-sm text-neutral-600 mt-0.5">{subtitle}</p>
          ) : (
            <div className="flex items-center gap-2 text-body-sm text-neutral-600 mt-0.5">
              <Calendar size={14} />
              <span>{currentDate}</span>
            </div>
          )}
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-3">
          {/* Search */}
          {showSearch && (
            <div className="relative">
              <input
                type="text"
                placeholder="Search insights..."
                className="w-64 pl-10 pr-4 py-2 rounded-lg border border-neutral-200 bg-neutral-50
                  text-body-sm text-neutral-950 placeholder:text-neutral-500
                  focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400
                  transition-all duration-200"
              />
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            </div>
          )}

          {/* Date Range Selector */}
          <button className="flex items-center gap-2 px-3 py-2 rounded-lg border border-neutral-200
            hover:bg-neutral-50 transition-colors text-body-sm text-neutral-700">
            <Calendar size={16} className="text-neutral-500" />
            <span>Last 30 days</span>
            <ChevronDown size={14} className="text-neutral-400" />
          </button>

          {/* AI Chat Button */}
          {onOpenChat && (
            <button
              onClick={onOpenChat}
              className="flex items-center gap-2 px-4 py-2 rounded-lg
                bg-brand-gradient
                text-white text-body-sm font-medium
                hover:opacity-90 transition-opacity"
            >
              <MessageSquare size={16} />
              <span>Ask AI</span>
            </button>
          )}

          {/* Notifications */}
          <button className="relative p-2 hover:bg-neutral-100 rounded-lg transition-colors">
            <Bell size={20} className="text-neutral-600" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-error-500 rounded-full" />
          </button>

          {/* User Avatar */}
          <button className="flex items-center gap-2 p-1.5 hover:bg-neutral-100 rounded-lg transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-purple to-brand-blue
              flex items-center justify-center text-white text-body-sm font-medium">
              <User size={16} />
            </div>
          </button>
        </div>
      </div>
    </header>
  );
}
