import { Card } from '@/components/common/Card'
import { Input } from '@/components/common/Input'
import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { User, Shield, Mic, Database, Key } from 'lucide-react'

const roles = [
  { name: 'Admin', permissions: ['read', 'write', 'approve', 'audit'], color: 'danger' as const },
  { name: 'Manager', permissions: ['read', 'write', 'approve'], color: 'warning' as const },
  { name: 'Analyst', permissions: ['read', 'write'], color: 'info' as const },
  { name: 'Viewer', permissions: ['read'], color: 'default' as const },
]

export function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Card>
        <div className="mb-4 flex items-center gap-2">
          <User className="h-5 w-5 text-accent-400" />
          <h3 className="text-sm font-semibold text-slate-200">Profile</h3>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Display Name" defaultValue="Enterprise Analyst" />
          <Input label="Email" defaultValue="analyst@enterprise.com" type="email" />
        </div>
      </Card>

      <Card>
        <div className="mb-4 flex items-center gap-2">
          <Shield className="h-5 w-5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-200">Role-Based Access Control</h3>
          <Badge variant="warning">Phase III</Badge>
        </div>
        <div className="space-y-3">
          {roles.map((role) => (
            <div
              key={role.name}
              className="flex items-center justify-between rounded-xl border border-surface-600/30 bg-surface-800/30 px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <Badge variant={role.color}>{role.name}</Badge>
                <span className="text-xs text-slate-500">
                  {role.permissions.join(' · ')}
                </span>
              </div>
              <input type="radio" name="role" defaultChecked={role.name === 'Analyst'} className="accent-cyan-400" />
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="mb-4 flex items-center gap-2">
          <Database className="h-5 w-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-200">API Configuration</h3>
        </div>
        <div className="space-y-4">
          <Input label="FastAPI Backend URL" defaultValue="http://localhost:8000" />
          <Input label="Gemini API Key" type="password" defaultValue="••••••••••••••••" />
        </div>
        <Button className="mt-4" variant="secondary">
          Save Configuration
        </Button>
      </Card>

      <Card>
        <div className="mb-4 flex items-center gap-2">
          <Mic className="h-5 w-5 text-red-400" />
          <h3 className="text-sm font-semibold text-slate-200">Voice Input</h3>
          <Badge variant="warning">Phase III</Badge>
        </div>
        <p className="text-sm text-slate-400">
          Enable hands-free natural language queries. Voice-to-query integration will connect to
          the browser Speech Recognition API and forward transcripts to the NL-to-SQL pipeline.
        </p>
        <label className="mt-4 flex items-center gap-3">
          <input type="checkbox" className="h-4 w-4 rounded accent-cyan-400" disabled />
          <span className="text-sm text-slate-500">Enable voice input (coming soon)</span>
        </label>
      </Card>

      <Card>
        <div className="mb-4 flex items-center gap-2">
          <Key className="h-5 w-5 text-amber-400" />
          <h3 className="text-sm font-semibold text-slate-200">Security Guardrails</h3>
        </div>
        <ul className="space-y-2 text-sm text-slate-400">
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Read-only queries allowed for Analyst role
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Write operations require manager approval
          </li>
          <li className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Autonomous actions logged to audit trail
          </li>
        </ul>
      </Card>
    </div>
  )
}
