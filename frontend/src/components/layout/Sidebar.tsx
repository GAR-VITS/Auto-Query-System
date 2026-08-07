import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquareText,
  BarChart3,
  ShieldCheck,
  Settings,
  Database,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import { APP_NAME, NAV_ITEMS } from '@/constants/navigation'

const iconMap = {
  LayoutDashboard,
  MessageSquareText,
  BarChart3,
  ShieldCheck,
  Settings,
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-surface-600/40 bg-surface-900/80 backdrop-blur-xl transition-all duration-300 ${collapsed ? 'w-[72px]' : 'w-64'}`}
    >
      <div className="flex items-center gap-3 border-b border-surface-600/40 px-4 py-5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-500 to-indigo-500 shadow-lg shadow-cyan-500/20">
          <Database className="h-5 w-5 text-white" />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <h1 className="truncate text-lg font-bold tracking-tight">{APP_NAME}</h1>
            <p className="truncate text-[10px] uppercase tracking-widest text-slate-500">
              Agentic AI Platform
            </p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV_ITEMS.map((item) => {
          const Icon = iconMap[item.icon as keyof typeof iconMap]
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-accent-500/15 text-accent-400 shadow-inner'
                    : 'text-slate-400 hover:bg-surface-700/50 hover:text-slate-200'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {!collapsed && (
                <div className="min-w-0">
                  <span className="block truncate">{item.label}</span>
                  {item.description && (
                    <span className="block truncate text-[10px] font-normal text-slate-500 group-hover:text-slate-400">
                      {item.description}
                    </span>
                  )}
                </div>
              )}
            </NavLink>
          )
        })}
      </nav>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mx-3 mb-4 flex items-center justify-center rounded-lg border border-surface-600/40 p-2 text-slate-400 transition hover:bg-surface-700/50 hover:text-slate-200"
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </button>
    </aside>
  )
}
