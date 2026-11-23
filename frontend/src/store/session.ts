/**
 * Zustand Session Store
 * Manages active user role, token, demo user switching, and light/dark theme.
 */

import { create } from 'zustand';
import { login as apiLogin } from '../lib/api';

export type UserRole = 'viewer' | 'branch_officer' | 'credit_manager' | 'admin';

export interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  role: UserRole;
  branch_id?: number | null;
}

interface SessionState {
  user: UserProfile;
  token: string | null;
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;
  switchRole: (role: UserRole) => Promise<void>;
  signOut: () => void;
}

const DEMO_USERS: Record<UserRole, { u: string; p: string }> = {
  viewer: { u: 'viewer@nexusdb.local', p: 'viewer123' },
  branch_officer: { u: 'officer@nexusdb.local', p: 'officer123' },
  credit_manager: { u: 'manager@nexusdb.local', p: 'manager123' },
  admin: { u: 'admin@nexusdb.local', p: 'admin123' },
};

const DEFAULT_USER: UserProfile = {
  user_id: '1',
  username: 'viewer@nexusdb.local',
  email: 'viewer@nexusdb.local',
  role: 'viewer',
  branch_id: null,
};

export const useSessionStore = create<SessionState>((set, get) => {
  // Initialize theme from localStorage or system preference
  const savedTheme = (typeof window !== 'undefined' ? localStorage.getItem('nexus_theme') : null) as 'light' | 'dark' | null;
  const initialTheme: 'light' | 'dark' = savedTheme || (
    typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  );

  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', initialTheme);
  }

  return {
    user: DEFAULT_USER,
    token: typeof localStorage !== 'undefined' ? localStorage.getItem('nexus_token') : null,
    theme: initialTheme,

    setTheme: (theme) => {
      localStorage.setItem('nexus_theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
      set({ theme });
    },

    toggleTheme: () => {
      const nextTheme = get().theme === 'light' ? 'dark' : 'light';
      get().setTheme(nextTheme);
    },

    switchRole: async (role: UserRole) => {
      const creds = DEMO_USERS[role];
      try {
        const resp = await apiLogin(creds.u, creds.p);
        localStorage.setItem('nexus_token', resp.access_token);
        set({
          token: resp.access_token,
          user: resp.user,
        });
      } catch (e) {
        // Fallback for offline demo mode
        set({
          user: {
            user_id: role === 'branch_officer' ? '2' : (role === 'credit_manager' ? '3' : (role === 'admin' ? '4' : '1')),
            username: creds.u,
            email: creds.u,
            role,
            branch_id: role === 'branch_officer' ? 1 : null,
          }
        });
      }
    },

    signOut: () => {
      localStorage.removeItem('nexus_token');
      set({ user: DEFAULT_USER, token: null });
    },
  };
});
