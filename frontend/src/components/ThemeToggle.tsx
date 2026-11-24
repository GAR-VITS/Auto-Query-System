import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useSessionStore } from '../store/session';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useSessionStore();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="p-1.5 rounded border border-line text-ink-2 hover:text-ink hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? (
        <Sun className="w-4 h-4 text-ink-2 hover:text-ink" />
      ) : (
        <Moon className="w-4 h-4 text-ink-2 hover:text-ink" />
      )}
    </button>
  );
};
