import { Lightbulb } from 'lucide-react'

interface SuggestedQueriesProps {
  suggestions: string[]
  onSelect: (query: string) => void
}

export function SuggestedQueries({ suggestions, onSelect }: SuggestedQueriesProps) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
        <Lightbulb className="h-4 w-4 text-amber-400" />
        Suggested queries
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((query) => (
          <button
            key={query}
            onClick={() => onSelect(query)}
            className="rounded-full border border-surface-600/40 bg-surface-800/40 px-3 py-1.5 text-xs text-slate-400 transition hover:border-accent-500/40 hover:bg-accent-500/10 hover:text-accent-300"
          >
            {query}
          </button>
        ))}
      </div>
    </div>
  )
}
