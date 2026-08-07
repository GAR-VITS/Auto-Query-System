import type { NavItem } from '@/types'

export const APP_NAME = 'NexusDB'
export const APP_TAGLINE = 'Autonomous Agentic AI for Enterprise Data'

export const NAV_ITEMS: NavItem[] = [
  {
    path: '/',
    label: 'Dashboard',
    icon: 'LayoutDashboard',
    description: 'Overview & agent status',
  },
  {
    path: '/query',
    label: 'Query Workspace',
    icon: 'MessageSquareText',
    description: 'Natural language to SQL',
  },
  {
    path: '/analytics',
    label: 'Analytics',
    icon: 'BarChart3',
    description: 'Charts & insights',
  },
  {
    path: '/audit',
    label: 'Audit Trail',
    icon: 'ShieldCheck',
    description: 'Compliance & decision logs',
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: 'Settings',
    description: 'Roles & preferences',
  },
]

export const SUGGESTED_QUERIES = [
  'Show all customers with credit score below 600',
  'List top 10 defaulters by outstanding loan amount',
  'What is the average repayment rate this quarter?',
  'Find loans approved in the last 30 days over ₹5 lakh',
  'Show transaction volume by region for Q4',
  'Which accounts have missed 3 or more EMI payments?',
]

export const AGENT_COLORS = {
  query: '#818cf8',
  analysis: '#34d399',
  visualization: '#fbbf24',
} as const
