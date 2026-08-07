import { Brain, Sparkles } from 'lucide-react'
import { Card } from '@/components/common/Card'

interface AnalysisPanelProps {
  analysis: string
}

export function AnalysisPanel({ analysis }: AnalysisPanelProps) {
  return (
    <Card className="border-indigo-500/20 bg-indigo-500/5">
      <div className="mb-3 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20">
          <Brain className="h-4 w-4 text-indigo-400" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-slate-200">Analysis Agent Summary</h4>
          <p className="text-[10px] text-slate-500">Plain-English interpretation via Pandas</p>
        </div>
        <Sparkles className="ml-auto h-4 w-4 text-indigo-400/60" />
      </div>
      <p className="text-sm leading-relaxed text-slate-300">{analysis}</p>
    </Card>
  )
}
