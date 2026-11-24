import React, { useState, useRef, useEffect } from 'react';
import { Shield, ChevronDown, Check } from 'lucide-react';
import { useSessionStore, type UserRole } from '../store/session';

const ROLES: Array<{ role: UserRole; label: string; desc: string }> = [
  { role: 'viewer', label: 'Viewer', desc: 'Read-only queries, no actions' },
  { role: 'branch_officer', label: 'Branch Officer', desc: 'Branch-scoped queries & account status' },
  { role: 'credit_manager', label: 'Credit Manager', desc: 'Global queries, risk flag management' },
  { role: 'admin', label: 'Admin', desc: 'Full system privileges & write-backs' },
];

export const RoleSwitcher: React.FC = () => {
  const { user, switchRole } = useSessionStore();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const currentRoleConfig = ROLES.find((r) => r.role === user.role) || ROLES[0];

  const handleSelectRole = async (r: UserRole) => {
    setIsOpen(false);
    if (r !== user.role) {
      await switchRole(r);
    }
  };

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded border border-line bg-surface hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer text-ink"
        title="Switch active user role"
      >
        <Shield className="w-3.5 h-3.5 text-accent" />
        <span className="font-medium">{currentRoleConfig.label}</span>
        {user.branch_id && (
          <span className="text-[10px] text-ink-3">#{user.branch_id}</span>
        )}
        <ChevronDown className="w-3 h-3 text-ink-3" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-60 rounded-lg border border-line bg-surface shadow-lg py-1 z-50 text-xs">
          <div className="px-3 py-1.5 border-b border-line text-[10px] font-mono uppercase tracking-wider text-ink-3">
            Switch Demo Role
          </div>
          {ROLES.map((item) => (
            <button
              key={item.role}
              type="button"
              onClick={() => handleSelectRole(item.role)}
              className="w-full text-left px-3 py-2 hover:bg-black/5 dark:hover:bg-white/5 flex items-start justify-between gap-2 transition-colors cursor-pointer"
            >
              <div>
                <div className="font-mono font-medium text-ink flex items-center gap-1.5">
                  <span>{item.label}</span>
                  {item.role === user.role && (
                    <Check className="w-3 h-3 text-accent" />
                  )}
                </div>
                <div className="text-[11px] text-ink-3 font-sans mt-0.5">
                  {item.desc}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
