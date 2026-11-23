import { useState, useEffect } from 'react';
import { useSessionStore } from './store/session';
import { SystemPopover } from './components/SystemPopover';
import { RoleSwitcher } from './components/RoleSwitcher';
import { ThemeToggle } from './components/ThemeToggle';
import { AskView } from './views/Ask';
import { AuditView } from './views/Audit';
import { SchemaView } from './views/Schema';
import { Sparkles, Database, History } from 'lucide-react';

type ActiveTab = 'ask' | 'audit' | 'schema';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('ask');
  const { token, switchRole } = useSessionStore();

  // On first mount, ensure session token is seeded for default demo role
  useEffect(() => {
    if (!token) {
      switchRole('viewer').catch(() => {});
    }
  }, [token, switchRole]);

  return (
    <div className="min-h-screen bg-bg text-ink flex flex-col font-sans transition-colors duration-150">
      {/* 48px Fixed Top Bar */}
      <header className="h-12 border-b border-line bg-surface/90 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-6 flex items-center justify-between">
        {/* Left: NexusDB wordmark + System Popover */}
        <div className="flex items-center gap-3">
          <SystemPopover />
        </div>

        {/* Center: 3-Tab Segment */}
        <nav className="flex items-center gap-1 sm:gap-6 h-full font-mono text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('ask')}
            className={`h-full px-3 flex items-center gap-1.5 border-b-2 transition-all cursor-pointer font-medium ${
              activeTab === 'ask'
                ? 'border-accent text-accent'
                : 'border-transparent text-ink-3 hover:text-ink'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('audit')}
            className={`h-full px-3 flex items-center gap-1.5 border-b-2 transition-all cursor-pointer font-medium ${
              activeTab === 'audit'
                ? 'border-accent text-accent'
                : 'border-transparent text-ink-3 hover:text-ink'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Log</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('schema')}
            className={`h-full px-3 flex items-center gap-1.5 border-b-2 transition-all cursor-pointer font-medium ${
              activeTab === 'schema'
                ? 'border-accent text-accent'
                : 'border-transparent text-ink-3 hover:text-ink'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Schema</span>
          </button>
        </nav>

        {/* Right: Demo Role Switcher + Theme Toggle */}
        <div className="flex items-center gap-2">
          <RoleSwitcher />
          <ThemeToggle />
        </div>
      </header>

      {/* Main View Area */}
      <main className="flex-1 w-full pb-16">
        {activeTab === 'ask' && <AskView />}
        {activeTab === 'audit' && <AuditView />}
        {activeTab === 'schema' && <SchemaView />}
      </main>
    </div>
  );
}
