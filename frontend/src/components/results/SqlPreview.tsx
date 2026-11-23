import { useState } from 'react'
import { ChevronDown, ChevronUp, Code2, Copy, Check } from 'lucide-react'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'

interface SqlPreviewProps {
  sql: string
  corrections?: number
}

export function SqlPreview({ sql, corrections }: SqlPreviewProps) {
  const [expanded, setExpanded] = useState(true)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card className="overflow-hidden p-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-5 py-3 text-left transition hover:bg-surface-700/30"
      >
        <div className="flex items-center gap-2">
          <Code2 className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-slate-300">Generated SQL</span>
          {corrections ? (
            <Badge variant="warning">{`${corrections} self-correction(s)`}</Badge>
          ) : null}
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-slate-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-500" />
        )}
      </button>

      {expanded && (
        <div className="relative border-t border-surface-600/40">
          <button
            onClick={handleCopy}
            className="absolute right-3 top-3 rounded-lg bg-surface-700/80 p-1.5 text-slate-400 transition hover:text-slate-200"
            title="Copy SQL"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
          <pre className="overflow-x-auto p-5 font-mono text-xs leading-relaxed text-emerald-300/90">
            {sql}
          </pre>
        </div>
      )}
    </Card>
  )
}
