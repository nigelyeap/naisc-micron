# React Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit frontend with a Vite + React + shadcn/ui SPA that connects to the existing FastAPI backend, using the Datadog/Grafana dark aesthetic with an icon-only sidebar.

**Architecture:** The React app lives in `frontend/` and calls the FastAPI backend at `http://localhost:8000`. A Vite dev proxy forwards all `/api/*` requests to the backend, eliminating CORS issues. The backend is not modified except for two new sample-log endpoints.

**Tech Stack:** React 18, Vite 5, TypeScript, Tailwind CSS v3, shadcn/ui, Recharts, TanStack Query v5, Axios, React Router v6, Lucide React, react-markdown

---

## File Map

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                      # shadcn/ui generated (do not edit manually)
│   │   ├── layout/
│   │   │   ├── Shell.tsx            # Root layout: sidebar + topbar + content
│   │   │   ├── Sidebar.tsx          # Icon-only 40px nav rail
│   │   │   └── TopBar.tsx           # Page title + API status + file count
│   │   └── shared/
│   │       ├── KpiCard.tsx          # Left-border KPI metric card
│   │       ├── SeverityBadge.tsx    # CRIT/WARN/INFO/OK coloured pill
│   │       ├── FormatBadge.tsx      # JSON/XML/CSV/etc neutral pill
│   │       └── ErrorBanner.tsx      # Inline API error display
│   ├── pages/
│   │   ├── OverviewPage.tsx         # KPIs + events feed + charts
│   │   ├── UploadPage.tsx           # File upload + sample quick-load
│   │   ├── ExplorerPage.tsx         # Filterable records table
│   │   ├── AnalyticsPage.tsx        # Charts dashboard
│   │   ├── NlQueryPage.tsx          # Natural language → SQL
│   │   ├── SummaryPage.tsx          # Markdown report
│   │   └── ArchitecturePage.tsx     # Pipeline SVG diagram
│   ├── lib/
│   │   ├── api.ts                   # Axios instance + all typed API functions
│   │   └── utils.ts                 # cn(), formatters
│   ├── App.tsx                      # QueryClientProvider + Router + Shell
│   ├── main.tsx                     # React DOM root
│   └── index.css                    # Tailwind directives + CSS design tokens
├── components.json                  # shadcn/ui config
├── package.json
├── vite.config.ts                   # Vite + /api proxy
├── tailwind.config.ts
└── tsconfig.json

backend/app.py                       # Add GET /api/samples + POST /api/samples/upload/{name}
run.py                               # Replace Streamlit launch with npm run dev
```

---

## Task 1: Scaffold the Vite + React + TypeScript project

**Files:**
- Create: `frontend/` (entire directory)
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/tsconfig.json`

- [ ] **Step 1: Create the Vite project**

Run from the project root (`NAISC Micron/`):
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install all dependencies**

```bash
cd frontend
npm install \
  react-router-dom \
  @tanstack/react-query \
  axios \
  recharts \
  lucide-react \
  react-markdown \
  tailwindcss@3 postcss autoprefixer
npm install -D @types/node
npx tailwindcss init -p
```

- [ ] **Step 3: Replace `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: Replace `frontend/tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-base':    'var(--bg-base)',
        'bg-panel':   'var(--bg-panel)',
        'bg-raised':  'var(--bg-raised)',
        border:       'var(--border)',
        'text-primary': 'var(--text-primary)',
        'text-muted':   'var(--text-muted)',
        'accent-blue':  'var(--accent-blue)',
        'accent-red':   'var(--accent-red)',
        'accent-amber': 'var(--accent-amber)',
        'accent-green': 'var(--accent-green)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}

export default config
```

- [ ] **Step 5: Replace `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 6: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: scaffold Vite + React + TypeScript frontend"
```

---

## Task 2: Configure shadcn/ui + design tokens

**Files:**
- Create: `frontend/components.json`
- Modify: `frontend/src/index.css`
- Create: `frontend/src/main.tsx`

- [ ] **Step 1: Initialise shadcn/ui**

```bash
cd frontend
npx shadcn@latest init
```

When prompted:
- Style: **Default**
- Base color: **Neutral**
- CSS variables: **Yes**

- [ ] **Step 2: Add all required shadcn components**

```bash
npx shadcn@latest add button badge card input select textarea separator tooltip collapsible scroll-area progress table
```

- [ ] **Step 3: Replace `frontend/src/index.css` with design tokens**

```css
@import url('https://fonts.bunny.net/css?family=inter:400,500,600,700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --bg-base:        #111318;
    --bg-panel:       #161a22;
    --bg-raised:      #1e2028;
    --border:         #1e2028;
    --text-primary:   #e2e8f0;
    --text-muted:     #64748b;
    --accent-blue:    #3b82f6;
    --accent-red:     #ef4444;
    --accent-amber:   #f59e0b;
    --accent-green:   #22c55e;

    /* shadcn/ui mappings */
    --background:     #111318;
    --foreground:     #e2e8f0;
    --card:           #161a22;
    --card-foreground:#e2e8f0;
    --popover:        #161a22;
    --popover-foreground: #e2e8f0;
    --primary:        #3b82f6;
    --primary-foreground: #fff;
    --secondary:      #1e2028;
    --secondary-foreground: #e2e8f0;
    --muted:          #1e2028;
    --muted-foreground: #64748b;
    --accent:         #1e2028;
    --accent-foreground: #e2e8f0;
    --destructive:    #ef4444;
    --destructive-foreground: #fff;
    --border-radius:  0.375rem;
    --input:          #1e2028;
    --ring:           #3b82f6;
    --radius:         0.5rem;
  }

  * {
    border-color: var(--border);
  }

  html, body, #root {
    height: 100%;
    background-color: var(--bg-base);
    color: var(--text-primary);
    font-family: 'Inter', system-ui, sans-serif;
  }

  /* Tabular nums for all metric-style text */
  [data-metric] {
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum";
  }
}
```

- [ ] **Step 4: Replace `frontend/src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

- [ ] **Step 5: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: configure shadcn/ui and design tokens"
```

---

## Task 3: Add sample log endpoints to FastAPI backend

**Files:**
- Modify: `backend/app.py` (add 2 endpoints after line 288)

The React upload page needs to list and trigger sample log uploads from the server filesystem. Two endpoints handle this.

- [ ] **Step 1: Add imports at the top of `backend/app.py`** (after existing imports, before `app = FastAPI(...)`)

Add `from pathlib import Path` to the imports block.

- [ ] **Step 2: Add the two endpoints to `backend/app.py`** (add after the `list_files` endpoint, around line 290)

```python
# -- Sample logs -------------------------------------------------------------

_SAMPLE_LOGS_DIR = Path(_PROJECT_ROOT) / "sample_logs"


@app.get("/api/samples")
def list_samples():
    """List available sample log filenames (non-.py files in sample_logs/)."""
    if not _SAMPLE_LOGS_DIR.is_dir():
        return []
    return [
        f.name
        for f in sorted(_SAMPLE_LOGS_DIR.iterdir())
        if f.suffix != ".py" and f.is_file()
    ]


@app.post("/api/samples/upload/{filename}", response_model=UploadResponse)
async def upload_sample(filename: str):
    """Parse and store a sample log file by name."""
    path = _SAMPLE_LOGS_DIR / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found.")
    # Reuse the upload logic by constructing an UploadFile-like call
    content = path.read_bytes()
    import io
    from starlette.datastructures import UploadFile as StarletteUploadFile
    fake_file = StarletteUploadFile(filename=filename, file=io.BytesIO(content))
    return await upload_file(fake_file)
```

- [ ] **Step 3: Restart the backend and verify**

```bash
python run.py --backend
```

Open `http://localhost:8000/api/samples` — should return a JSON array of filenames like:
```json
["binary_diagnostic.bin","euv_dose_recipe.xml","event_log.txt",...]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app.py
git commit -m "feat: add sample log list and upload endpoints"
```

---

## Task 4: API client and types

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/utils.ts`

- [ ] **Step 1: Create `frontend/src/lib/utils.ts`**

```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTimestamp(ts: string | null): string {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}

export function formatConfidence(v: number): string {
  return `${(v * 100).toFixed(1)}%`
}

export function formatMs(ms: number): string {
  return ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(2)}s`
}
```

Install clsx and tailwind-merge (required by shadcn/ui's `cn` utility):
```bash
cd frontend && npm install clsx tailwind-merge
```

- [ ] **Step 2: Create `frontend/src/lib/api.ts`**

```typescript
import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

// ---- Types -----------------------------------------------------------------

export interface LogFile {
  id: number
  filename: string
  format_detected: string | null
  upload_time: string
  total_records: number
  avg_confidence: number
  parse_time_ms: number
}

export interface LogRecord {
  id: number
  file_id: number
  source_format: string
  timestamp: string | null
  tool_id: string | null
  module_id: string | null
  event_type: string | null
  severity: string | null
  parameters_json: string | null
  raw_content: string | null
  confidence: number
  parse_warnings_json: string | null
}

export interface Anomaly {
  id: number
  record_id: number
  parameter: string
  value: number
  expected_min: number
  expected_max: number
  anomaly_type: string
  severity: string
  z_score: number
  description: string
  detected_at: string
}

export interface UploadResponse {
  file_id: number
  filename: string
  format_detected: string | null
  total_records: number
  avg_confidence: number
  parse_time_ms: number
  anomalies_found: number
}

export interface SummaryStats {
  total_files: number
  total_records: number
  total_anomalies: number
  avg_confidence: number
  event_type_breakdown: Record<string, number>
  severity_breakdown: Record<string, number>
  tool_breakdown: Record<string, number>
}

export interface TimeseriesPoint {
  timestamp: string
  tool_id: string
  parameter: string
  value: number
}

export interface TimeseriesResponse {
  parameter: string
  tool_id: string | null
  data: TimeseriesPoint[]
}

export interface NLQueryResponse {
  generated_sql: string
  results: Record<string, unknown>[]
  explanation: string
  confidence: number
}

export interface HealthResponse {
  status: string
  database: string
  parser_available: boolean
  analytics_available: boolean
  nl_query_mode: string
}

export interface RecordFilters {
  tool_id?: string
  event_type?: string
  severity?: string
  file_id?: number
  limit?: number
  offset?: number
}

// ---- API functions ---------------------------------------------------------

export const api = {
  health: () =>
    http.get<HealthResponse>('/health').then(r => r.data),

  uploadFile: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post<UploadResponse>('/upload', fd).then(r => r.data)
  },

  uploadSample: (filename: string) =>
    http.post<UploadResponse>(`/samples/upload/${encodeURIComponent(filename)}`).then(r => r.data),

  listSamples: () =>
    http.get<string[]>('/samples').then(r => r.data),

  listFiles: () =>
    http.get<LogFile[]>('/files').then(r => r.data),

  getRecords: (filters: RecordFilters = {}) =>
    http.get<LogRecord[]>('/records', { params: filters }).then(r => r.data),

  getRecord: (id: number) =>
    http.get<LogRecord>(`/records/${id}`).then(r => r.data),

  getAnomalies: () =>
    http.get<Anomaly[]>('/anomalies').then(r => r.data),

  getSummary: () =>
    http.get<SummaryStats>('/analytics/summary').then(r => r.data),

  getTimeseries: (parameter: string, tool_id?: string) =>
    http.get<TimeseriesResponse>('/analytics/timeseries', {
      params: { parameter, tool_id },
    }).then(r => r.data),

  nlQuery: (question: string) =>
    http.post<NLQueryResponse>('/query', { question }).then(r => r.data),
}
```

- [ ] **Step 3: Commit**

```bash
cd ..
git add frontend/src/lib/
git commit -m "feat: add typed API client and utility functions"
```

---

## Task 5: Shared components

**Files:**
- Create: `frontend/src/components/shared/KpiCard.tsx`
- Create: `frontend/src/components/shared/SeverityBadge.tsx`
- Create: `frontend/src/components/shared/FormatBadge.tsx`
- Create: `frontend/src/components/shared/ErrorBanner.tsx`

- [ ] **Step 1: Create `frontend/src/components/shared/KpiCard.tsx`**

```tsx
interface KpiCardProps {
  label: string
  value: string | number
  accent: 'blue' | 'red' | 'amber' | 'green'
  sub?: string
}

const accentBorder: Record<KpiCardProps['accent'], string> = {
  blue:  'border-l-accent-blue',
  red:   'border-l-accent-red',
  amber: 'border-l-accent-amber',
  green: 'border-l-accent-green',
}

const accentText: Record<KpiCardProps['accent'], string> = {
  blue:  'text-accent-blue',
  red:   'text-accent-red',
  amber: 'text-accent-amber',
  green: 'text-accent-green',
}

export function KpiCard({ label, value, accent, sub }: KpiCardProps) {
  return (
    <div className={`bg-bg-panel border-l-2 ${accentBorder[accent]} px-4 py-3`}>
      <p className="text-text-muted text-[11px] font-medium uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className={`text-2xl font-bold tabular-nums ${accentText[accent]}`}>
        {value}
      </p>
      {sub && (
        <p className="text-text-muted text-xs mt-1">{sub}</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/shared/SeverityBadge.tsx`**

```tsx
type Severity = 'CRIT' | 'CRITICAL' | 'WARN' | 'WARNING' | 'INFO' | 'OK' | 'DEBUG' | string

interface SeverityBadgeProps { value: string | null }

function normalise(s: string): Severity {
  const u = s.toUpperCase()
  if (u === 'CRITICAL') return 'CRIT'
  if (u === 'WARNING')  return 'WARN'
  return u as Severity
}

const styles: Record<string, string> = {
  CRIT:  'bg-red-500/10 text-accent-red',
  WARN:  'bg-amber-500/10 text-accent-amber',
  INFO:  'bg-blue-500/10 text-accent-blue',
  OK:    'bg-green-500/10 text-accent-green',
  DEBUG: 'bg-gray-500/10 text-text-muted',
}

export function SeverityBadge({ value }: SeverityBadgeProps) {
  if (!value) return <span className="text-text-muted text-xs">—</span>
  const norm = normalise(value)
  const cls = styles[norm] ?? 'bg-gray-500/10 text-text-muted'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide ${cls}`}>
      {norm}
    </span>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/shared/FormatBadge.tsx`**

```tsx
interface FormatBadgeProps { value: string | null }

export function FormatBadge({ value }: FormatBadgeProps) {
  if (!value) return <span className="text-text-muted text-xs">—</span>
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded bg-bg-raised text-text-muted text-[11px] font-mono uppercase tracking-wide">
      {value}
    </span>
  )
}
```

- [ ] **Step 4: Create `frontend/src/components/shared/ErrorBanner.tsx`**

```tsx
import { AlertCircle } from 'lucide-react'

interface ErrorBannerProps { message?: string }

export function ErrorBanner({ message = 'Failed to load data.' }: ErrorBannerProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded text-accent-red text-sm">
      <AlertCircle className="w-4 h-4 shrink-0" />
      {message}
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/shared/
git commit -m "feat: add KpiCard, SeverityBadge, FormatBadge, ErrorBanner components"
```

---

## Task 6: Shell layout

**Files:**
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/TopBar.tsx`
- Create: `frontend/src/components/layout/Shell.tsx`

- [ ] **Step 1: Create `frontend/src/components/layout/Sidebar.tsx`**

```tsx
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Upload, Table, BarChart2,
  MessageSquare, FileText, Cpu,
} from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const NAV = [
  { to: '/',             icon: LayoutDashboard, label: 'Overview'     },
  { to: '/upload',       icon: Upload,          label: 'Upload'       },
  { to: '/explorer',     icon: Table,           label: 'Explorer'     },
  { to: '/analytics',    icon: BarChart2,        label: 'Analytics'   },
  { to: '/query',        icon: MessageSquare,   label: 'NL Query'     },
  { to: '/summary',      icon: FileText,        label: 'Summary'      },
  { to: '/architecture', icon: Cpu,             label: 'Architecture' },
]

export function Sidebar() {
  return (
    <TooltipProvider delayDuration={200}>
      <nav className="w-10 shrink-0 bg-[#0d1017] border-r border-border flex flex-col items-center py-3 gap-1">
        {/* Logo mark */}
        <div className="w-6 h-6 rounded bg-accent-blue flex items-center justify-center mb-3">
          <span className="text-white text-[10px] font-bold">SL</span>
        </div>
        {NAV.map(({ to, icon: Icon, label }) => (
          <Tooltip key={to}>
            <TooltipTrigger asChild>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `w-8 h-8 rounded flex items-center justify-center transition-colors ${
                    isActive
                      ? 'bg-accent-blue/20 text-accent-blue'
                      : 'text-text-muted hover:text-text-primary hover:bg-bg-raised'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
              </NavLink>
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-bg-raised text-text-primary border-border text-xs">
              {label}
            </TooltipContent>
          </Tooltip>
        ))}
      </nav>
    </TooltipProvider>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/layout/TopBar.tsx`**

```tsx
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface TopBarProps { title: string }

export function TopBar({ title }: TopBarProps) {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30_000,
    retry: false,
  })

  const { data: files } = useQuery({
    queryKey: ['files'],
    queryFn: api.listFiles,
    refetchInterval: 10_000,
  })

  const connected = health?.status === 'ok'

  return (
    <header className="h-10 border-b border-border bg-bg-base flex items-center px-4 shrink-0">
      <h1 className="text-text-primary text-sm font-semibold tracking-tight flex-1">{title}</h1>
      <div className="flex items-center gap-4 text-xs text-text-muted">
        {files !== undefined && (
          <span>{files.length} file{files.length !== 1 ? 's' : ''} loaded</span>
        )}
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-accent-green' : 'bg-accent-red'}`} />
          <span>{connected ? 'API connected' : 'API unavailable'}</span>
        </div>
      </div>
    </header>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/layout/Shell.tsx`**

```tsx
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

const PAGE_TITLES: Record<string, string> = {
  '/':             'Overview',
  '/upload':       'Upload & Parse',
  '/explorer':     'Log Explorer',
  '/analytics':    'Analytics',
  '/query':        'Natural Language Query',
  '/summary':      'Summary Report',
  '/architecture': 'Architecture',
}

export function Shell() {
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] ?? 'Smart Log Parser'
  return (
    <div className="flex h-screen bg-bg-base overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar title={title} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/
git commit -m "feat: add Shell, Sidebar, and TopBar layout components"
```

---

## Task 7: App router

**Files:**
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/src/App.tsx`**

```tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Shell } from '@/components/layout/Shell'
import { OverviewPage }      from '@/pages/OverviewPage'
import { UploadPage }        from '@/pages/UploadPage'
import { ExplorerPage }      from '@/pages/ExplorerPage'
import { AnalyticsPage }     from '@/pages/AnalyticsPage'
import { NlQueryPage }       from '@/pages/NlQueryPage'
import { SummaryPage }       from '@/pages/SummaryPage'
import { ArchitecturePage }  from '@/pages/ArchitecturePage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      { index: true,          element: <OverviewPage /> },
      { path: 'upload',       element: <UploadPage /> },
      { path: 'explorer',     element: <ExplorerPage /> },
      { path: 'analytics',    element: <AnalyticsPage /> },
      { path: 'query',        element: <NlQueryPage /> },
      { path: 'summary',      element: <SummaryPage /> },
      { path: 'architecture', element: <ArchitecturePage /> },
    ],
  },
])

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  )
}
```

Create placeholder stubs for all pages so the app compiles (replace in later tasks):

- [ ] **Step 2: Create page stubs**

Create each of these files with the following content (substitute the name):

`frontend/src/pages/OverviewPage.tsx`:
```tsx
export function OverviewPage() { return <div className="text-text-primary">Overview</div> }
```

Repeat for `UploadPage`, `ExplorerPage`, `AnalyticsPage`, `NlQueryPage`, `SummaryPage`, `ArchitecturePage` (same pattern, change export name and text).

- [ ] **Step 3: Verify the app starts**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` — you should see a dark shell with the icon sidebar and "Overview" text in the main area. All nav icons should route without errors.

- [ ] **Step 4: Commit**

```bash
cd ..
git add frontend/src/App.tsx frontend/src/pages/
git commit -m "feat: add router, QueryClient, and page stubs"
```

---

## Task 8: Overview page

**Files:**
- Modify: `frontend/src/pages/OverviewPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/OverviewPage.tsx`**

```tsx
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { KpiCard } from '@/components/shared/KpiCard'
import { SeverityBadge } from '@/components/shared/SeverityBadge'
import { FormatBadge } from '@/components/shared/FormatBadge'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { formatTimestamp, formatConfidence } from '@/lib/utils'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const FORMAT_COLORS: Record<string, string> = {
  json:    '#3b82f6',
  xml:     '#f59e0b',
  csv:     '#22c55e',
  syslog:  '#a855f7',
  kv:      '#06b6d4',
  text:    '#64748b',
  binary:  '#ef4444',
}

export function OverviewPage() {
  const { data: summary, error: summaryErr } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
  })

  const { data: records, error: recordsErr } = useQuery({
    queryKey: ['records', { limit: 20 }],
    queryFn: () => api.getRecords({ limit: 20 }),
  })

  const severityData = summary
    ? Object.entries(summary.severity_breakdown).map(([k, v]) => ({ name: k || 'null', value: v }))
    : []

  const formatData = summary
    ? Object.entries(summary.tool_breakdown).map(([k, v]) => ({ name: k || 'unknown', value: v }))
    : []

  return (
    <div className="space-y-6">
      {(summaryErr || recordsErr) && <ErrorBanner message="Could not load overview data." />}

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard label="Total Records"  value={summary?.total_records ?? '—'} accent="blue" />
        <KpiCard label="Files Ingested" value={summary?.total_files ?? '—'} accent="green" />
        <KpiCard label="Anomalies"      value={summary?.total_anomalies ?? '—'} accent="red" />
        <KpiCard
          label="Avg Confidence"
          value={summary ? formatConfidence(summary.avg_confidence) : '—'}
          accent="amber"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Severity distribution */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-4">Severity Distribution</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={severityData} barSize={24}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip
                contentStyle={{ background: '#1e2028', border: '1px solid #1e2028', color: '#e2e8f0', fontSize: 12 }}
                cursor={{ fill: '#1e2028' }}
              />
              <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                {severityData.map((entry, i) => {
                  const c = entry.name.toUpperCase()
                  const fill = c.includes('CRIT') ? '#ef4444' : c.includes('WARN') ? '#f59e0b' : c.includes('INFO') ? '#3b82f6' : '#64748b'
                  return <Cell key={i} fill={fill} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Tool breakdown */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-4">Records by Tool</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={formatData} layout="vertical" barSize={14}>
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
              <Tooltip
                contentStyle={{ background: '#1e2028', border: '1px solid #1e2028', color: '#e2e8f0', fontSize: 12 }}
                cursor={{ fill: '#1e2028' }}
              />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent events */}
      <div className="bg-bg-panel border border-border">
        <div className="px-4 py-3 border-b border-border bg-bg-raised">
          <p className="text-text-muted text-[11px] uppercase tracking-wider">Recent Events</p>
        </div>
        <div className="divide-y divide-border">
          {(records ?? []).map(rec => (
            <div key={rec.id} className="flex items-center gap-4 px-4 py-2.5 text-sm hover:bg-bg-raised transition-colors">
              <span className="text-text-muted text-xs w-36 shrink-0 font-mono">
                {formatTimestamp(rec.timestamp)}
              </span>
              <span className="text-text-muted w-24 shrink-0 truncate text-xs">{rec.tool_id ?? '—'}</span>
              <span className="text-text-primary flex-1 truncate">{rec.event_type ?? rec.raw_content?.slice(0, 60) ?? '—'}</span>
              <FormatBadge value={rec.source_format} />
              <SeverityBadge value={rec.severity} />
            </div>
          ))}
          {!records?.length && (
            <p className="px-4 py-6 text-text-muted text-sm text-center">No records yet. Upload a log file to get started.</p>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/OverviewPage.tsx
git commit -m "feat: implement Overview page"
```

---

## Task 9: Upload page

**Files:**
- Modify: `frontend/src/pages/UploadPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/UploadPage.tsx`**

```tsx
import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, FileCheck, AlertTriangle } from 'lucide-react'
import { api, UploadResponse } from '@/lib/api'
import { FormatBadge } from '@/components/shared/FormatBadge'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { formatMs, formatConfidence } from '@/lib/utils'

export function UploadPage() {
  const qc = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [results, setResults] = useState<UploadResponse[]>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const { data: samples = [] } = useQuery({
    queryKey: ['samples'],
    queryFn: api.listSamples,
  })

  async function handleFiles(files: FileList | File[]) {
    setUploading(true)
    setError(null)
    const arr = Array.from(files)
    const newResults: UploadResponse[] = []
    for (const file of arr) {
      try {
        const res = await api.uploadFile(file)
        newResults.push(res)
      } catch {
        setError(`Failed to upload "${file.name}"`)
      }
    }
    setResults(prev => [...newResults, ...prev])
    qc.invalidateQueries()
    setUploading(false)
  }

  async function handleSample(name: string) {
    setUploading(true)
    setError(null)
    try {
      const res = await api.uploadSample(name)
      setResults(prev => [res, ...prev])
      qc.invalidateQueries()
    } catch {
      setError(`Failed to load sample "${name}"`)
    }
    setUploading(false)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {error && <ErrorBanner message={error} />}

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files) }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded cursor-pointer flex flex-col items-center justify-center py-14 transition-colors ${
          dragOver ? 'border-accent-blue bg-accent-blue/5' : 'border-border hover:border-accent-blue/50 hover:bg-bg-panel'
        }`}
      >
        <Upload className="w-8 h-8 text-text-muted mb-3" />
        <p className="text-text-primary font-medium">Drop log files here or click to browse</p>
        <p className="text-text-muted text-sm mt-1">JSON, XML, CSV, Syslog, Key-Value, Text, Binary</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={e => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {uploading && (
        <div className="flex items-center gap-3 text-text-muted text-sm">
          <div className="w-4 h-4 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
          Parsing...
        </div>
      )}

      {/* Sample logs */}
      <div>
        <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Quick Demo — Sample Logs</p>
        <div className="flex flex-wrap gap-2">
          {samples.filter(n => !n.endsWith('.py')).map(name => (
            <Button
              key={name}
              variant="outline"
              size="sm"
              disabled={uploading}
              onClick={() => handleSample(name)}
              className="bg-bg-panel border-border text-text-muted hover:text-text-primary hover:bg-bg-raised text-xs font-mono"
            >
              {name}
            </Button>
          ))}
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div>
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Parse Results</p>
          <div className="space-y-3">
            {results.map((r, i) => (
              <div key={i} className="bg-bg-panel border border-border p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <FileCheck className="w-4 h-4 text-accent-green shrink-0" />
                  <span className="text-text-primary font-medium flex-1 truncate">{r.filename}</span>
                  <FormatBadge value={r.format_detected} />
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Records</p>
                    <p className="text-text-primary font-semibold tabular-nums">{r.total_records}</p>
                  </div>
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Anomalies</p>
                    <p className={`font-semibold tabular-nums ${r.anomalies_found > 0 ? 'text-accent-red' : 'text-text-muted'}`}>
                      {r.anomalies_found}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Parse Time</p>
                    <p className="text-text-primary font-semibold">{formatMs(r.parse_time_ms)}</p>
                  </div>
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Confidence</p>
                    <p className="text-text-primary font-semibold">{formatConfidence(r.avg_confidence)}</p>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-text-muted">
                    <span>Confidence</span>
                    <span>{formatConfidence(r.avg_confidence)}</span>
                  </div>
                  <Progress
                    value={r.avg_confidence * 100}
                    className="h-1.5 bg-bg-raised [&>div]:bg-accent-blue"
                  />
                </div>
                {r.anomalies_found > 0 && (
                  <div className="flex items-center gap-2 text-accent-amber text-xs">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    {r.anomalies_found} anomal{r.anomalies_found === 1 ? 'y' : 'ies'} detected
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/UploadPage.tsx
git commit -m "feat: implement Upload page"
```

---

## Task 10: Explorer page

**Files:**
- Modify: `frontend/src/pages/ExplorerPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/ExplorerPage.tsx`**

```tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, X } from 'lucide-react'
import { api, LogRecord } from '@/lib/api'
import { SeverityBadge } from '@/components/shared/SeverityBadge'
import { FormatBadge } from '@/components/shared/FormatBadge'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { formatTimestamp, formatConfidence } from '@/lib/utils'

const PAGE_SIZES = [25, 50, 100]

export function ExplorerPage() {
  const [toolId, setToolId]     = useState('')
  const [severity, setSeverity] = useState('')
  const [format, setFormat]     = useState('')
  const [limit, setLimit]       = useState(50)
  const [offset, setOffset]     = useState(0)
  const [expanded, setExpanded] = useState<number | null>(null)

  const filters = {
    tool_id:   toolId   || undefined,
    severity:  severity || undefined,
    source_format: format || undefined,
    limit,
    offset,
  }

  const { data: records = [], error, isFetching } = useQuery({
    queryKey: ['records', filters],
    queryFn: () => api.getRecords(filters),
  })

  function clearFilters() {
    setToolId(''); setSeverity(''); setFormat(''); setOffset(0)
  }

  function toggleExpand(id: number) {
    setExpanded(prev => prev === id ? null : id)
  }

  function parseParams(json: string | null): Record<string, unknown> {
    if (!json) return {}
    try { return JSON.parse(json) } catch { return {} }
  }

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message="Failed to load records." />}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Input
          placeholder="Tool ID"
          value={toolId}
          onChange={e => { setToolId(e.target.value); setOffset(0) }}
          className="w-36 bg-bg-panel border-border text-text-primary placeholder:text-text-muted h-8 text-sm"
        />
        <Select value={severity} onValueChange={v => { setSeverity(v === 'all' ? '' : v); setOffset(0) }}>
          <SelectTrigger className="w-32 bg-bg-panel border-border text-text-primary h-8 text-sm">
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent className="bg-bg-panel border-border text-text-primary">
            <SelectItem value="all">All</SelectItem>
            {['CRITICAL', 'WARNING', 'INFO', 'OK', 'DEBUG'].map(s => (
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={format} onValueChange={v => { setFormat(v === 'all' ? '' : v); setOffset(0) }}>
          <SelectTrigger className="w-32 bg-bg-panel border-border text-text-primary h-8 text-sm">
            <SelectValue placeholder="Format" />
          </SelectTrigger>
          <SelectContent className="bg-bg-panel border-border text-text-primary">
            <SelectItem value="all">All</SelectItem>
            {['json','xml','csv','syslog','kv','text','binary'].map(f => (
              <SelectItem key={f} value={f}>{f.toUpperCase()}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="ghost" size="sm" onClick={clearFilters} className="text-text-muted hover:text-text-primary h-8">
          <X className="w-3.5 h-3.5 mr-1" /> Clear
        </Button>
        {isFetching && <div className="w-3.5 h-3.5 border-2 border-accent-blue border-t-transparent rounded-full animate-spin ml-auto" />}
      </div>

      {/* Table */}
      <div className="bg-bg-panel border border-border overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[24px_1fr_120px_100px_80px_80px_70px] items-center px-3 py-2 bg-bg-raised border-b border-border text-[11px] text-text-muted uppercase tracking-wider font-medium">
          <span />
          <span>Event</span>
          <span>Timestamp</span>
          <span>Tool</span>
          <span>Format</span>
          <span>Severity</span>
          <span>Conf.</span>
        </div>

        <div className="divide-y divide-border">
          {records.map(rec => (
            <div key={rec.id}>
              <div
                className="grid grid-cols-[24px_1fr_120px_100px_80px_80px_70px] items-center px-3 py-2.5 hover:bg-bg-raised cursor-pointer transition-colors text-sm"
                onClick={() => toggleExpand(rec.id)}
              >
                <span className="text-text-muted">
                  {expanded === rec.id
                    ? <ChevronDown className="w-3.5 h-3.5" />
                    : <ChevronRight className="w-3.5 h-3.5" />}
                </span>
                <span className="text-text-primary truncate pr-2">{rec.event_type ?? rec.raw_content?.slice(0, 60) ?? '—'}</span>
                <span className="text-text-muted text-xs font-mono">{formatTimestamp(rec.timestamp)}</span>
                <span className="text-text-muted text-xs truncate">{rec.tool_id ?? '—'}</span>
                <FormatBadge value={rec.source_format} />
                <SeverityBadge value={rec.severity} />
                <span className="text-text-muted text-xs tabular-nums">{formatConfidence(rec.confidence)}</span>
              </div>

              {expanded === rec.id && (
                <div className="bg-bg-base border-t border-border px-6 py-4 text-xs space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-text-muted mb-1 uppercase tracking-wider">Tool / Module</p>
                      <p className="text-text-primary font-mono">{rec.tool_id ?? '—'} / {rec.module_id ?? '—'}</p>
                    </div>
                    <div>
                      <p className="text-text-muted mb-1 uppercase tracking-wider">Timestamp</p>
                      <p className="text-text-primary font-mono">{rec.timestamp ?? '—'}</p>
                    </div>
                  </div>
                  {rec.parameters_json && Object.keys(parseParams(rec.parameters_json)).length > 0 && (
                    <div>
                      <p className="text-text-muted mb-1 uppercase tracking-wider">Parameters</p>
                      <pre className="bg-bg-raised border border-border rounded p-3 text-text-primary font-mono overflow-x-auto">
                        {JSON.stringify(parseParams(rec.parameters_json), null, 2)}
                      </pre>
                    </div>
                  )}
                  {rec.raw_content && (
                    <div>
                      <p className="text-text-muted mb-1 uppercase tracking-wider">Raw Content</p>
                      <pre className="bg-bg-raised border border-border rounded p-3 text-text-muted font-mono overflow-x-auto whitespace-pre-wrap">
                        {rec.raw_content.slice(0, 500)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {records.length === 0 && (
            <p className="px-4 py-8 text-text-muted text-sm text-center">No records match the current filters.</p>
          )}
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-text-muted text-xs">
          Rows per page:
          {PAGE_SIZES.map(s => (
            <button
              key={s}
              onClick={() => { setLimit(s); setOffset(0) }}
              className={`px-2 py-0.5 rounded ${limit === s ? 'bg-accent-blue/20 text-accent-blue' : 'hover:bg-bg-raised text-text-muted'}`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline" size="sm"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - limit))}
            className="bg-bg-panel border-border text-text-muted hover:bg-bg-raised h-7 text-xs"
          >
            Prev
          </Button>
          <span className="text-text-muted text-xs">
            {offset + 1}–{offset + records.length}
          </span>
          <Button
            variant="outline" size="sm"
            disabled={records.length < limit}
            onClick={() => setOffset(offset + limit)}
            className="bg-bg-panel border-border text-text-muted hover:bg-bg-raised h-7 text-xs"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ExplorerPage.tsx
git commit -m "feat: implement Explorer page with filters and expandable rows"
```

---

## Task 11: Analytics page

**Files:**
- Modify: `frontend/src/pages/AnalyticsPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/AnalyticsPage.tsx`**

```tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend, LineChart, Line,
} from 'recharts'

const CHART_COLORS = ['#3b82f6', '#f59e0b', '#22c55e', '#ef4444', '#a855f7', '#06b6d4', '#64748b']

export function AnalyticsPage() {
  const [tsParam, setTsParam] = useState('temperature')

  const { data: summary, error: summaryErr } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
  })

  const { data: timeseries, error: tsErr } = useQuery({
    queryKey: ['timeseries', tsParam],
    queryFn: () => api.getTimeseries(tsParam),
    enabled: !!tsParam,
  })

  const severityData = summary
    ? Object.entries(summary.severity_breakdown).map(([k, v]) => ({ name: k || 'null', value: v }))
    : []

  const eventData = summary
    ? Object.entries(summary.event_type_breakdown).map(([k, v]) => ({ name: k || 'null', value: v }))
    : []

  const toolData = summary
    ? Object.entries(summary.tool_breakdown).map(([k, v]) => ({ name: k || 'unknown', count: v }))
    : []

  const tsData = (timeseries?.data ?? []).map(p => ({
    time: p.timestamp ? new Date(p.timestamp).toLocaleTimeString() : '',
    value: typeof p.value === 'number' ? p.value : null,
    tool: p.tool_id,
  }))

  return (
    <div className="space-y-6">
      {(summaryErr || tsErr) && <ErrorBanner message="Some analytics data failed to load." />}

      <div className="grid grid-cols-2 gap-4">
        {/* Severity distribution */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-4">Severity Distribution</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={severityData} barSize={28}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
              <Tooltip contentStyle={{ background: '#1e2028', border: 'none', color: '#e2e8f0', fontSize: 12 }} cursor={{ fill: '#1e2028' }} />
              <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                {severityData.map((e, i) => {
                  const u = e.name.toUpperCase()
                  const fill = u.includes('CRIT') ? '#ef4444' : u.includes('WARN') ? '#f59e0b' : u.includes('INFO') ? '#3b82f6' : '#64748b'
                  return <Cell key={i} fill={fill} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Event type breakdown */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-4">Event Types</p>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={eventData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75} innerRadius={40}>
                {eventData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e2028', border: 'none', color: '#e2e8f0', fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Parameter timeseries */}
        <div className="bg-bg-panel border border-border p-4 col-span-2">
          <div className="flex items-center justify-between mb-4">
            <p className="text-text-muted text-[11px] uppercase tracking-wider">Parameter Timeseries</p>
            <input
              value={tsParam}
              onChange={e => setTsParam(e.target.value)}
              placeholder="parameter name"
              className="bg-bg-raised border border-border text-text-primary text-xs px-2 py-1 rounded w-40 outline-none focus:border-accent-blue"
            />
          </div>
          {tsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={tsData}>
                <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={40} />
                <Tooltip contentStyle={{ background: '#1e2028', border: 'none', color: '#e2e8f0', fontSize: 12 }} />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" dot={false} strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-text-muted text-sm text-center py-12">
              No timeseries data for "{tsParam}". Try "temperature", "pressure", or "dose".
            </p>
          )}
        </div>

        {/* Cross-tool comparison */}
        <div className="bg-bg-panel border border-border p-4 col-span-2">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-4">Records by Tool</p>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={toolData} layout="vertical" barSize={14}>
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
              <Tooltip contentStyle={{ background: '#1e2028', border: 'none', color: '#e2e8f0', fontSize: 12 }} cursor={{ fill: '#1e2028' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/AnalyticsPage.tsx
git commit -m "feat: implement Analytics page with charts"
```

---

## Task 12: NL Query page

**Files:**
- Modify: `frontend/src/pages/NlQueryPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/NlQueryPage.tsx`**

```tsx
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, ChevronDown, ChevronUp } from 'lucide-react'
import { api, NLQueryResponse } from '@/lib/api'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

const PRESETS = [
  'Show me all alarm events',
  'What is the average temperature per tool?',
  'Show the most recent anomalies',
  'How many records were parsed per file format?',
]

export function NlQueryPage() {
  const [question, setQuestion] = useState('')
  const [sqlOpen, setSqlOpen]   = useState(false)
  const [result, setResult]     = useState<NLQueryResponse | null>(null)

  const { mutate, isPending, error } = useMutation({
    mutationFn: (q: string) => api.nlQuery(q),
    onSuccess: data => { setResult(data); setSqlOpen(false) },
  })

  function submit() {
    if (!question.trim()) return
    mutate(question.trim())
  }

  const columns = result?.results[0] ? Object.keys(result.results[0]) : []

  return (
    <div className="space-y-5 max-w-2xl">
      {/* Preset chips */}
      <div>
        <p className="text-text-muted text-[11px] uppercase tracking-wider mb-2">Example queries</p>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map(p => (
            <button
              key={p}
              onClick={() => setQuestion(p)}
              className="text-xs bg-bg-panel border border-border text-text-muted hover:text-text-primary hover:border-accent-blue/50 px-3 py-1.5 rounded transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <Textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask anything about your log data in plain English..."
          rows={3}
          className="bg-bg-panel border-border text-text-primary placeholder:text-text-muted resize-none focus:border-accent-blue"
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit() }}
        />
        <div className="flex items-center justify-between">
          <p className="text-text-muted text-xs">Cmd/Ctrl + Enter to submit</p>
          <Button
            onClick={submit}
            disabled={isPending || !question.trim()}
            size="sm"
            className="bg-accent-blue hover:bg-blue-500 text-white"
          >
            {isPending
              ? <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              : <Send className="w-3.5 h-3.5 mr-2" />}
            Query
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message="Query failed. Is the API running?" />}

      {result && (
        <div className="space-y-4">
          {/* Explanation */}
          {result.explanation && (
            <p className="text-text-muted text-sm">{result.explanation}</p>
          )}

          {/* SQL collapsible */}
          <div className="bg-bg-panel border border-border rounded overflow-hidden">
            <button
              onClick={() => setSqlOpen(o => !o)}
              className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-text-muted hover:bg-bg-raised transition-colors"
            >
              <span className="uppercase tracking-wider">Generated SQL</span>
              {sqlOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            {sqlOpen && (
              <pre className="px-4 py-3 border-t border-border text-xs font-mono text-accent-green bg-bg-base overflow-x-auto">
                {result.generated_sql}
              </pre>
            )}
          </div>

          {/* Results table */}
          {result.results.length > 0 ? (
            <div className="bg-bg-panel border border-border overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg-raised border-b border-border">
                    {columns.map(c => (
                      <th key={c} className="text-left px-3 py-2 text-[11px] text-text-muted uppercase tracking-wider font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {result.results.map((row, i) => (
                    <tr key={i} className="hover:bg-bg-raised transition-colors">
                      {columns.map(c => (
                        <td key={c} className="px-3 py-2 text-text-primary font-mono text-xs">
                          {String(row[c] ?? '—')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-text-muted text-sm text-center py-6 bg-bg-panel border border-border">
              Query returned no results.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/NlQueryPage.tsx
git commit -m "feat: implement NL Query page"
```

---

## Task 13: Summary page

**Files:**
- Modify: `frontend/src/pages/SummaryPage.tsx`

- [ ] **Step 1: Install react-markdown (if not already installed)**

```bash
cd frontend && npm install react-markdown
```

- [ ] **Step 2: Replace `frontend/src/pages/SummaryPage.tsx`**

```tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api, SummaryStats } from '@/lib/api'
import { KpiCard } from '@/components/shared/KpiCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Button } from '@/components/ui/button'
import { formatConfidence } from '@/lib/utils'

function buildMarkdown(s: SummaryStats): string {
  const sevLines = Object.entries(s.severity_breakdown)
    .map(([k, v]) => `- **${k || 'null'}**: ${v}`)
    .join('\n')
  const eventLines = Object.entries(s.event_type_breakdown)
    .map(([k, v]) => `- **${k || 'null'}**: ${v}`)
    .join('\n')
  const toolLines = Object.entries(s.tool_breakdown)
    .map(([k, v]) => `- **${k || 'unknown'}**: ${v} records`)
    .join('\n')

  return `# Smart Tool Log Parser — Summary Report

## Overview

| Metric | Value |
|--------|-------|
| Total Files | ${s.total_files} |
| Total Records | ${s.total_records} |
| Total Anomalies | ${s.total_anomalies} |
| Average Confidence | ${formatConfidence(s.avg_confidence)} |

## Severity Breakdown

${sevLines || '_No data_'}

## Event Types

${eventLines || '_No data_'}

## Tool Performance

${toolLines || '_No data_'}

## Key Findings

- Parsed **${s.total_records}** log records across **${s.total_files}** files
- Detected **${s.total_anomalies}** anomalies requiring attention
- Average parse confidence: **${formatConfidence(s.avg_confidence)}**
- Formats supported: JSON, XML, CSV, Syslog, Key-Value, Plain Text, Binary
`
}

export function SummaryPage() {
  const [generated, setGenerated] = useState(false)

  const { data: summary, error, refetch, isFetching } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
    enabled: generated,
  })

  function generate() {
    setGenerated(true)
    refetch()
  }

  function exportMd() {
    if (!summary) return
    const md = buildMarkdown(summary)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `slp-summary-${new Date().toISOString().slice(0, 10)}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {error && <ErrorBanner message="Failed to load summary." />}

      <div className="flex items-center gap-3">
        <Button
          onClick={generate}
          disabled={isFetching}
          className="bg-accent-blue hover:bg-blue-500 text-white"
        >
          {isFetching
            ? <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
            : <RefreshCw className="w-3.5 h-3.5 mr-2" />}
          Generate Report
        </Button>
        {summary && (
          <Button
            variant="outline"
            onClick={exportMd}
            className="bg-bg-panel border-border text-text-muted hover:text-text-primary hover:bg-bg-raised"
          >
            <Download className="w-3.5 h-3.5 mr-2" />
            Export .md
          </Button>
        )}
      </div>

      {summary && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <KpiCard label="Files"      value={summary.total_files}    accent="blue" />
            <KpiCard label="Records"    value={summary.total_records}  accent="green" />
            <KpiCard label="Anomalies"  value={summary.total_anomalies} accent="red" />
            <KpiCard label="Confidence" value={formatConfidence(summary.avg_confidence)} accent="amber" />
          </div>

          <div className="bg-bg-panel border border-border p-6 prose prose-invert prose-sm max-w-none
            [&_h1]:text-text-primary [&_h1]:text-lg [&_h1]:font-semibold [&_h1]:mb-4
            [&_h2]:text-text-primary [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:uppercase [&_h2]:tracking-wider [&_h2]:mt-6 [&_h2]:mb-3
            [&_p]:text-text-muted [&_p]:text-sm [&_li]:text-text-muted [&_li]:text-sm
            [&_strong]:text-text-primary [&_code]:text-accent-green [&_code]:font-mono
            [&_table]:w-full [&_th]:text-left [&_th]:text-text-muted [&_th]:text-[11px] [&_th]:uppercase [&_th]:tracking-wider [&_th]:pb-2
            [&_td]:text-text-primary [&_td]:text-sm [&_td]:py-1.5 [&_td]:border-b [&_td]:border-border
            [&_hr]:border-border">
            <ReactMarkdown>{buildMarkdown(summary)}</ReactMarkdown>
          </div>
        </>
      )}

      {!generated && (
        <p className="text-text-muted text-sm text-center py-12 bg-bg-panel border border-border">
          Click "Generate Report" to produce a summary of all parsed data.
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
cd ..
git add frontend/src/pages/SummaryPage.tsx
git commit -m "feat: implement Summary Report page"
```

---

## Task 14: Architecture page

**Files:**
- Modify: `frontend/src/pages/ArchitecturePage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/ArchitecturePage.tsx`**

```tsx
const STAGES = [
  {
    id: 'input',
    label: 'Raw Log Files',
    color: '#64748b',
    sub: ['JSON', 'XML', 'CSV', 'Syslog', 'KV', 'Text', 'Binary'],
    desc: 'Semiconductor equipment logs from diverse vendors in 7 formats',
  },
  {
    id: 'detector',
    label: 'Format Detector',
    color: '#a855f7',
    sub: ['Byte patterns', 'Regex heuristics', 'Statistical analysis'],
    desc: 'Content-based detection — no file extension required',
  },
  {
    id: 'parser',
    label: 'Parser',
    color: '#3b82f6',
    sub: ['JSONParser', 'XMLParser', 'CSVParser', 'SyslogParser', 'KVParser', 'TextParser', 'BinaryParser'],
    desc: 'Per-format parsers with recursive flattening and LLM fallback',
  },
  {
    id: 'schema',
    label: 'Schema Inferencer',
    color: '#06b6d4',
    sub: ['Field mapping', 'Vendor normalisation'],
    desc: 'Maps vendor-specific fields to the unified semiconductor schema',
  },
  {
    id: 'normaliser',
    label: 'Normalizer',
    color: '#22c55e',
    sub: ['UnifiedLogRecord', 'Timestamp', 'Severity', 'Parameters'],
    desc: 'Produces consistent UnifiedLogRecord instances for all formats',
  },
  {
    id: 'db',
    label: 'SQLite DB',
    color: '#f59e0b',
    sub: ['log_files', 'log_records', 'anomalies'],
    desc: 'WAL-mode SQLite with thread-safe connections',
  },
  {
    id: 'api',
    label: 'FastAPI',
    color: '#ef4444',
    sub: ['11 endpoints', 'NL → SQL', 'Anomaly detection'],
    desc: 'REST API with Claude-powered natural language queries',
  },
  {
    id: 'ui',
    label: 'React UI',
    color: '#3b82f6',
    sub: ['Overview', 'Explorer', 'Analytics', 'NL Query', 'Summary'],
    desc: 'This dashboard — Vite + shadcn/ui + Recharts',
  },
]

export function ArchitecturePage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-text-primary text-lg font-semibold mb-1">Pipeline Architecture</h2>
        <p className="text-text-muted text-sm">
          End-to-end flow from raw semiconductor equipment logs to queryable structured data.
        </p>
      </div>

      {/* Pipeline flow */}
      <div className="overflow-x-auto pb-4">
        <div className="flex items-start gap-0 min-w-max">
          {STAGES.map((stage, i) => (
            <div key={stage.id} className="flex items-center">
              {/* Stage box */}
              <div className="w-40 bg-bg-panel border border-border rounded p-3 flex flex-col gap-2">
                <div
                  className="text-xs font-semibold text-center py-1.5 px-2 rounded"
                  style={{ background: stage.color + '20', color: stage.color }}
                >
                  {stage.label}
                </div>
                <div className="flex flex-col gap-1">
                  {stage.sub.map(s => (
                    <div key={s} className="text-[10px] text-text-muted bg-bg-raised px-1.5 py-0.5 rounded font-mono">
                      {s}
                    </div>
                  ))}
                </div>
                <p className="text-[10px] text-text-muted leading-relaxed border-t border-border pt-2 mt-1">
                  {stage.desc}
                </p>
              </div>
              {/* Arrow */}
              {i < STAGES.length - 1 && (
                <div className="flex items-center mx-1 mt-6">
                  <div className="w-4 h-px bg-border" />
                  <div
                    className="w-0 h-0"
                    style={{
                      borderTop: '4px solid transparent',
                      borderBottom: '4px solid transparent',
                      borderLeft: '5px solid #1e2028',
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Component table */}
      <div className="bg-bg-panel border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-bg-raised">
          <p className="text-text-muted text-[11px] uppercase tracking-wider">Component Reference</p>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-2.5 text-[11px] text-text-muted uppercase tracking-wider font-medium">Component</th>
              <th className="text-left px-4 py-2.5 text-[11px] text-text-muted uppercase tracking-wider font-medium">File(s)</th>
              <th className="text-left px-4 py-2.5 text-[11px] text-text-muted uppercase tracking-wider font-medium">Responsibility</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {[
              ['Format Detector', 'parser/format_detector.py', 'Content-based format identification'],
              ['Parser Pipeline', 'parser/pipeline.py', 'Orchestrates detect → parse → normalize'],
              ['JSON Parser',     'parser/parsers/json_parser.py', 'Recursive nested JSON flattening'],
              ['XML Parser',      'parser/parsers/xml_parser.py', 'ElementTree-based extraction'],
              ['CSV Parser',      'parser/parsers/csv_parser.py', 'Standard CSV with header inference'],
              ['Syslog Parser',   'parser/parsers/syslog_parser.py', 'RFC 3164/5424 parsing'],
              ['KV Parser',       'parser/parsers/kv_parser.py', 'Key=value regex extraction'],
              ['Text Parser',     'parser/parsers/text_parser.py', 'Unstructured text pattern matching'],
              ['Binary Parser',   'parser/parsers/binary_parser.py', 'Hex dump + embedded string extraction'],
              ['LLM Fallback',    'parser/llm_fallback.py', 'Claude API for unknown formats'],
              ['Schema Inferencer','parser/schema_inferencer.py', 'Maps vendor fields to unified schema'],
              ['Normalizer',      'parser/normalizer.py', 'Produces UnifiedLogRecord instances'],
              ['Anomaly Detector','analytics/anomaly_detector.py', 'Z-score, IQR, rate-of-change detection'],
              ['Trend Analyzer',  'analytics/trend_analyzer.py', 'Linear regression + drift detection'],
              ['Fault Correlator','analytics/fault_correlator.py', 'Alarm-to-anomaly correlation'],
              ['Database',        'backend/database.py', 'SQLite WAL-mode thread-safe wrapper'],
              ['NL Query Engine', 'backend/nl_query.py', 'English → SQL via Claude API'],
              ['FastAPI App',     'backend/app.py', '11-endpoint REST API'],
              ['React Frontend',  'frontend/src/', 'This dashboard'],
            ].map(([comp, file, desc]) => (
              <tr key={comp} className="hover:bg-bg-raised transition-colors">
                <td className="px-4 py-2.5 text-text-primary font-medium">{comp}</td>
                <td className="px-4 py-2.5 text-accent-green font-mono text-xs">{file}</td>
                <td className="px-4 py-2.5 text-text-muted">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ArchitecturePage.tsx
git commit -m "feat: implement Architecture page with pipeline diagram"
```

---

## Task 15: Update run.py

**Files:**
- Modify: `run.py`

- [ ] **Step 1: Replace `run.py`**

```python
"""
Central entry point -- starts the FastAPI backend and React frontend together.

Usage:
    python run.py            # starts both backend + frontend
    python run.py --backend  # backend only
    python run.py --frontend # frontend only
"""

import os
import sys
import time
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


def start_backend():
    """Launch the FastAPI/uvicorn backend as a subprocess."""
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app",
         "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=PROJECT_ROOT,
    )


def start_frontend():
    """Launch the Vite dev server."""
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    return subprocess.Popen(
        [npm, "run", "dev"],
        cwd=FRONTEND_DIR,
    )


def main():
    parser = argparse.ArgumentParser(description="Smart Log Parser -- Launcher")
    parser.add_argument("--backend",  action="store_true", help="Start backend only")
    parser.add_argument("--frontend", action="store_true", help="Start frontend only")
    args = parser.parse_args()

    run_backend  = not args.frontend or args.backend
    run_frontend = not args.backend  or args.frontend
    if not args.backend and not args.frontend:
        run_backend = run_frontend = True

    procs = []

    try:
        if run_backend:
            print("[SLP] Starting backend  → http://localhost:8000")
            procs.append(start_backend())

        if run_frontend:
            if run_backend:
                time.sleep(2)
            print("[SLP] Starting frontend → http://localhost:5173")
            procs.append(start_frontend())

        print("[SLP] All services running. Press Ctrl+C to stop.\n")

        while True:
            for p in procs:
                ret = p.poll()
                if ret is not None:
                    print(f"\n[SLP] A process exited with code {ret}")
                    raise SystemExit(ret)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[SLP] Shutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            p.wait(timeout=5)
        print("[SLP] Stopped.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the full stack starts**

```bash
python run.py
```

Expected output:
```
[SLP] Starting backend  → http://localhost:8000
[SLP] Starting frontend → http://localhost:5173
[SLP] All services running. Press Ctrl+C to stop.
```

Open `http://localhost:5173` — the full app should load with real data from the backend.

- [ ] **Step 3: Commit**

```bash
git add run.py
git commit -m "feat: update run.py to launch Vite frontend instead of Streamlit"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] H aesthetic (Datadog/Grafana dark) — design tokens in Task 2
- [x] Icon-only sidebar — Task 6
- [x] Overview page — Task 8
- [x] Upload page with sample quick-load — Tasks 3 + 9
- [x] Explorer with filters + expandable rows + pagination — Task 10
- [x] Analytics with 4 charts — Task 11
- [x] NL Query page — Task 12
- [x] Summary report + export — Task 13
- [x] Architecture page — Task 14
- [x] Vite proxy to FastAPI — Task 1
- [x] TanStack Query — Tasks 4, 7
- [x] shadcn/ui components — Task 2
- [x] run.py updated — Task 15

**No placeholders found.**

**Type consistency:** All types defined in `lib/api.ts` (Task 4) and used consistently across all pages. `LogRecord`, `SummaryStats`, `UploadResponse`, `NLQueryResponse` match the backend Pydantic models exactly.
