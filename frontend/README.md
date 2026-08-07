# NexusDB — Agentic Enterprise Platform

React + Vite frontend for the **Self-Correcting Multi-Agent Framework for Natural Language Database Navigation and Autonomous Enterprise Workflow Execution** project.

## Features

- **Dashboard** — Agent status, stats, recent queries, project roadmap
- **Query Workspace** — Natural language to SQL with mock agent pipeline
- **Analytics** — Chart.js visualizations (loan risk, repayment rates, agent success)
- **Audit Trail** — Compliance logs with agent reasoning
- **Settings** — RBAC roles, API config, voice input placeholder

## Tech Stack

- React 19 + TypeScript
- Vite 8
- Tailwind CSS 4
- React Router 7
- Chart.js + react-chartjs-2
- Framer Motion
- Lucide React icons

## Project Structure

```
src/
├── components/
│   ├── audit/          # Audit log components
│   ├── charts/         # Chart.js wrappers
│   ├── common/         # Reusable UI (Button, Card, Badge...)
│   ├── dashboard/      # Dashboard widgets
│   ├── layout/         # Sidebar, Header, MainLayout
│   ├── query/          # NL query input & suggestions
│   └── results/        # Data tables, SQL preview, analysis
├── constants/          # Navigation, app config
├── data/               # Mock data for offline demo
├── hooks/              # useQuery hook
├── pages/              # Route pages
├── services/           # API layer (falls back to mock)
└── types/              # TypeScript interfaces
```

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Backend Integration

Set `VITE_API_URL` in `.env` to your FastAPI backend:

```env
VITE_API_URL=http://localhost:8000
```

Expected endpoints:
- `POST /api/query` — `{ question, voice? }` → `{ success, result?, error? }`
- `GET /health` — Health check

When the backend is unavailable, the app uses mock data automatically.

## Build

```bash
npm run build
npm run preview
```
