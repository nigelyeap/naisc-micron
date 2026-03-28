# React Frontend Redesign — Smart Tool Log Parser
**Date:** 2026-03-28
**Status:** Approved

---

## Overview

Replace the existing Streamlit frontend with a React SPA that connects to the unchanged FastAPI backend. The new frontend uses the Datadog/Grafana dark aesthetic (H), an icon-only sidebar layout, and shadcn/ui components on Tailwind CSS.

---

## 1. Architecture & Stack

### Directory structure

```
NAISC Micron/
├── backend/          # unchanged (FastAPI + SQLite)
├── parser/           # unchanged
├── analytics/        # unchanged
├── sample_logs/      # unchanged
├── frontend/         # NEW — replaces app.py and views/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/           # shadcn/ui generated components
│   │   │   ├── layout/       # Shell, Sidebar, TopBar
│   │   │   └── shared/       # KpiCard, SeverityBadge, FormatBadge, ErrorBanner
│   │   ├── pages/
│   │   │   ├── OverviewPage.tsx
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ExplorerPage.tsx
│   │   │   ├── AnalyticsPage.tsx
│   │   │   ├── NlQueryPage.tsx
│   │   │   ├── SummaryPage.tsx
│   │   │   └── ArchitecturePage.tsx
│   │   ├── lib/
│   │   │   ├── api.ts        # Axios instance + typed API functions
│   │   │   └── utils.ts      # cn(), formatters
│   │   ├── App.tsx           # Router + Shell
│   │   ├── main.tsx
│   │   └── index.css         # Tailwind directives + CSS variables
│   ├── components.json       # shadcn/ui config
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── run.py            # updated to start both servers
└── app.py            # removed
```

### Tech stack

| Layer | Tool | Version |
|---|---|---|
| Framework | React | 18 |
| Build tool | Vite | 5 |
| Routing | React Router | v6 |
| Components | shadcn/ui (Radix + Tailwind) | latest |
| Charts | Recharts | 2 |
| Data fetching | TanStack Query | v5 |
| HTTP client | Axios | 1 |
| Icons | Lucide React | latest |
| Fonts | Inter via Bunny Fonts | — |

---

## 2. Pages & Components

### Shell (persistent)

- **Sidebar** (40px wide): icon-only nav rail, active icon highlighted with `--accent-blue` background, tooltips on hover showing page name. Icons from Lucide React.
- **TopBar**: page title on left, API connection status dot + file count on right.
- **Content area**: fills remaining width, scrollable per-page.

### Pages

#### Overview (`/`)
- Icon: `LayoutDashboard`
- 4 KPI cards in a row: Total Records (blue), Warnings (amber), Critical (red), Avg Confidence (green)
- Recent events feed: timestamp + tool_id + event + severity badge, last 20 records
- Format breakdown: horizontal bar chart by source_format
- Anomaly timeline: Recharts AreaChart of anomaly counts over time

#### Upload (`/upload`)
- Icon: `Upload`
- Drag-and-drop zone (dashed border, accept any file)
- Quick-load buttons for each sample log in `sample_logs/`
- Parse result cards: filename, format badge, confidence progress bar, record count, parse time, warnings collapsible

#### Explorer (`/explorer`)
- Icon: `Table`
- Filter row: tool_id select, severity select, format select, limit input, clear button
- shadcn/ui Table: columns = timestamp, tool_id, event_type, severity badge, format badge, confidence
- Expandable row: full record detail (parameters JSON, raw content, parse warnings)
- Client-side pagination: rows-per-page select (25 / 50 / 100), prev/next buttons

#### Analytics (`/analytics`)
- Icon: `BarChart2`
- Severity distribution: Recharts BarChart
- Event type breakdown: Recharts PieChart
- Parameter timeseries: Recharts LineChart (parameter selector dropdown)
- Cross-tool comparison: horizontal bar chart from `/api/analytics/cross-tool`

#### NL Query (`/query`)
- Icon: `MessageSquare`
- Prompt textarea + Send button
- Preset query chips: "Show all alarm events", "Average temperature per tool", "Most recent anomalies", "Files ingested today"
- Generated SQL: shadcn/ui Collapsible with monospace code block
- Query explanation text
- Results: shadcn/ui Table, dynamic columns from response

#### Summary (`/summary`)
- Icon: `FileText`
- Generate button → `GET /api/analytics/summary` → renders markdown
- Sections: overview stats, anomaly list, trend highlights, key findings
- Export as `.md` button (client-side download)

#### Architecture (`/architecture`)
- Icon: `Cpu`
- Static SVG pipeline diagram illustrating the full parse flow:
  `Raw Log Files → Format Detector → Parser (JSON/XML/CSV/Syslog/KV/Text/Binary) → Schema Inferencer → Normalizer → SQLite DB → FastAPI → React UI`
- Callout boxes for each component with a one-line description
- Satisfies the hackathon deliverable for "detailed illustration of design architecture"

---

## 3. Data Flow

All persistent state lives in SQLite via the FastAPI backend. The React app is stateless beyond UI interactions.

### API client (`lib/api.ts`)
- Axios instance with `baseURL` from `VITE_API_URL` (defaults to `http://localhost:8000`)
- Typed wrapper functions for all 11 endpoints
- TanStack Query wraps every call for caching, loading states, and background refetch

### Key flows

| Action | API call | Side effect |
|---|---|---|
| File upload | `POST /api/upload` | Invalidates all queries → KPIs refresh |
| Explorer filter change | `GET /api/records?...` | Table re-renders, no navigation |
| Analytics mount | `GET /api/analytics/summary` + `/timeseries` + `/trends` + `/cross-tool` (parallel) | Charts render |
| NL Query submit | `POST /api/query` | SQL + results displayed inline |
| Summary generate | `GET /api/analytics/summary` | Markdown rendered |

### Error handling
- Every TanStack Query error state renders an `<ErrorBanner>` inside the relevant panel
- No full-page crashes — failed panels degrade independently
- Network errors show "API unavailable" in the TopBar status indicator

---

## 4. Design System

### CSS variables (`index.css`)

```css
:root {
  --bg-base:       #111318;  /* page background */
  --bg-panel:      #161a22;  /* cards, panels */
  --bg-raised:     #1e2028;  /* table headers, hover */
  --border:        #1e2028;  /* all borders */
  --text-primary:  #e2e8f0;  /* headings, values */
  --text-muted:    #64748b;  /* labels, secondary */
  --accent-blue:   #3b82f6;  /* primary actions, active nav */
  --accent-red:    #ef4444;  /* critical severity, anomalies */
  --accent-amber:  #f59e0b;  /* warning severity */
  --accent-green:  #22c55e;  /* healthy/info severity */
}
```

### Typography
- Font: Inter (Bunny Fonts CDN — no Google tracking)
- Metric values: `font-variant-numeric: tabular-nums`
- Labels: 11px, uppercase, letter-spacing 0.05em, `--text-muted`

### KPI card pattern
`bg-panel` background + 2px left border in accent colour + label (`text-muted`, 11px uppercase) + value (`text-primary`, 24px bold, tabular nums)

### Severity badge pattern
Pill with coloured text + low-opacity matching background:
- `CRIT` → red text, red/10 bg
- `WARN` → amber text, amber/10 bg
- `INFO` → blue text, blue/10 bg
- `OK` → green text, green/10 bg

### Format badge pattern
Neutral pill (`bg-raised`, `text-muted`) showing format name in uppercase monospace.

### shadcn/ui components used
Table, Badge, Button, Input, Card, Separator, Tooltip, Collapsible, ScrollArea, Select, Textarea, Progress

---

## 5. run.py update

`run.py` updated to launch both servers:
1. `uvicorn backend.app:app --port 8000` (existing)
2. `npm run dev --prefix frontend` (new, port 5173)

Both run concurrently via `subprocess` with `threading`.

---

## 6. Out of scope

- Authentication / login
- Real-time WebSocket updates
- Mobile responsiveness (desktop-first for hackathon)
- Dark/light mode toggle
- Unit tests for frontend components
