import { Bell, Circle, Search, User } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { NAV_ITEMS } from '@/constants/navigation'
import { Badge } from '@/components/common/Badge'

export function Header() {
  const location = useLocation()
  const currentPage = NAV_ITEMS.find(
    (item) => item.path === location.pathname || (item.path !== '/' && location.pathname.startsWith(item.path)),
  ) ?? NAV_ITEMS[0]

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-surface-600/40 bg-surface-900/60 px-6 backdrop-blur-xl">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">{currentPage.label}</h2>
        {currentPage.description && (
          <p className="text-xs text-slate-500">{currentPage.description}</p>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 rounded-xl border border-surface-600/40 bg-surface-800/50 px-3 py-2 md:flex">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Quick search..."
            className="w-48 bg-transparent text-sm text-slate-300 outline-none placeholder:text-slate-600"
          />
          <kbd className="rounded border border-surface-600 px-1.5 py-0.5 text-[10px] text-slate-500">
            ⌘K
          </kbd>
        </div>

        <Badge variant="success" dot>
          Backend Offline (Mock)
        </Badge>

        <button className="relative rounded-xl p-2 text-slate-400 transition hover:bg-surface-700/50 hover:text-slate-200">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-accent-400" />
        </button>

        <div className="flex items-center gap-3 rounded-xl border border-surface-600/40 bg-surface-800/50 px-3 py-1.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
            <User className="h-4 w-4 text-white" />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-slate-200">Analyst</p>
            <p className="flex items-center gap-1 text-[10px] text-slate-500">
              <Circle className="h-1.5 w-1.5 fill-emerald-400 text-emerald-400" />
              analyst@enterprise.com
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
