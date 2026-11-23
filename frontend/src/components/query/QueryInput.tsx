import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Send, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { StatusIndicator } from '@/components/common/StatusIndicator'
import type { AgentStatus } from '@/types'

interface QueryInputProps {
  onSubmit: (question: string, voice?: boolean) => void
  loading: boolean
  agentStatus: AgentStatus
}

export function QueryInput({ onSubmit, loading, agentStatus }: QueryInputProps) {
  const [question, setQuestion] = useState('')
  const [voiceActive, setVoiceActive] = useState(false)
  const [voiceTranscript, setVoiceTranscript] = useState('')
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    // Check for browser Speech Recognition API
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onresult = (event: any) => {
        let interim = ''
        let final = ''

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript
          } else {
            interim += event.results[i][0].transcript
          }
        }

        const newText = final || interim
        if (newText) {
          setVoiceTranscript(newText)
          setQuestion((prev) => (final ? (prev ? `${prev} ${final}` : final) : prev))
        }
      }

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error)
        setVoiceActive(false)
      }

      recognition.onend = () => {
        setVoiceActive(false)
      }

      recognitionRef.current = recognition
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          // ignore
        }
      }
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return
    if (voiceActive && recognitionRef.current) {
      recognitionRef.current.stop()
      setVoiceActive(false)
    }
    onSubmit(question.trim(), voiceActive)
  }

  const toggleVoice = () => {
    if (!recognitionRef.current) {
      // Fallback message if browser has no speech API
      setVoiceActive(!voiceActive)
      return
    }

    if (voiceActive) {
      try {
        recognitionRef.current.stop()
      } catch {
        // ignore
      }
      setVoiceActive(false)
    } else {
      try {
        setVoiceTranscript('Listening...')
        recognitionRef.current.start()
        setVoiceActive(true)
      } catch {
        setVoiceActive(false)
      }
    }
  }

  return (
    <Card glow className="relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-accent-500/5 via-transparent to-indigo-500/5" />

      <div className="relative">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent-400" />
            <h3 className="text-lg font-semibold text-slate-100">Ask Your Database</h3>
          </div>
          {(loading || agentStatus !== 'idle') && (
            <StatusIndicator status={agentStatus} />
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Show all customers with credit score below 600 who have active loans..."
              rows={3}
              disabled={loading}
              className="w-full resize-none rounded-xl border border-surface-600/60 bg-surface-900/60 px-4 py-3 pr-12 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition focus:border-accent-500/50 focus:ring-2 focus:ring-accent-500/20 disabled:opacity-60"
            />
            <button
              type="button"
              onClick={toggleVoice}
              className={`absolute right-3 top-3 rounded-lg p-2 transition ${
                voiceActive
                  ? 'bg-red-500/20 text-red-400 animate-pulse'
                  : 'text-slate-500 hover:bg-surface-700 hover:text-slate-300'
              }`}
              title={voiceActive ? 'Stop voice input' : 'Start voice input (Speech-to-Text)'}
            >
              {voiceActive ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>
          </div>

          {voiceActive && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="flex items-center gap-2 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400"
            >
              <span className="h-2 w-2 animate-pulse rounded-full bg-red-400" />
              {voiceTranscript || 'Listening... Speak your database query now.'}
            </motion.div>
          )}

          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Powered by Gemini 2.5 Flash · PostgreSQL & SQLite · Natural language to SQL
            </p>
            <Button type="submit" loading={loading} icon={<Send className="h-4 w-4" />}>
              Run Query
            </Button>
          </div>
        </form>
      </div>
    </Card>
  )
}
