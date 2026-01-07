import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  GitBranch,
  Sliders,
  MessageSquare,
  Settings,
  HelpCircle,
  ChevronLeft
} from 'lucide-react';
import { Logo } from '../ui/Logo';

interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard, path: '/' },
  { id: 'what-if', label: 'What-If', icon: Sliders, path: '/what-if' },
  { id: 'chat', label: 'AI Chat', icon: MessageSquare, path: '/ai-chat' },
  { id: 'deep-dive', label: 'Deep Dive', icon: Search, path: '/deep-dive' },
  { id: 'decomposition', label: 'Decomposition', icon: GitBranch, path: '/decomposition' },
];

const bottomNavItems = [
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
  { id: 'help', label: 'Help', icon: HelpCircle, path: '/help' },
];

export function Sidebar({
  collapsed = false,
  onToggleCollapse
}: SidebarProps) {
  return (
    <aside className={`
      fixed left-0 top-0 h-screen bg-white border-r border-neutral-100
      flex flex-col transition-all duration-300 z-40
      ${collapsed ? 'w-[72px]' : 'w-64'}
    `}>
      {/* Header */}
      <div className={`p-4 border-b border-neutral-100 flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
        <Logo size="md" showText={!collapsed} />
        {!collapsed && onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="p-1.5 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <ChevronLeft size={18} className="text-neutral-500" />
          </button>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.id}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                transition-all duration-200 text-left
                ${isActive
                  ? 'bg-primary-50 text-primary-500 font-medium'
                  : 'text-neutral-700 hover:bg-neutral-50 hover:text-neutral-950'
                }
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? item.label : undefined}
            >
              {({ isActive }) => (
                <>
                  <Icon size={20} className={isActive ? 'text-primary-500' : 'text-neutral-500'} />
                  {!collapsed && <span className="text-body-sm">{item.label}</span>}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-3 border-t border-neutral-100" />

      {/* Bottom Navigation */}
      <nav className="p-3 space-y-1">
        {bottomNavItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.id}
              to={item.path}
              className={({ isActive }) => `
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                transition-all duration-200 text-left
                ${isActive
                  ? 'bg-primary-50 text-primary-500 font-medium'
                  : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-950'
                }
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={20} className="text-neutral-500" />
              {!collapsed && <span className="text-body-sm">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse Toggle (when collapsed) */}
      {collapsed && onToggleCollapse && (
        <div className="p-3 border-t border-neutral-100">
          <button
            onClick={onToggleCollapse}
            className="w-full p-2.5 hover:bg-neutral-100 rounded-lg transition-colors flex justify-center"
          >
            <ChevronLeft size={18} className="text-neutral-500 rotate-180" />
          </button>
        </div>
      )}
    </aside>
  );
}
