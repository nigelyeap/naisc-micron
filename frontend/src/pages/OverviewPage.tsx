import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { KpiCard } from '@/components/shared/KpiCard'
import { SeverityBadge } from '@/components/shared/SeverityBadge'
import { FormatBadge } from '@/components/shared/FormatBadge'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { formatTimestamp, formatConfidence, formatMs } from '@/lib/utils'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend,
} from 'recharts'

const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: '#ef4444', CRIT: '#ef4444',
  WARNING: '#f59e0b', WARN: '#f59e0b',
  INFO: '#3b82f6',
  OK: '#22c55e',
}

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#22c55e', '#ef4444', '#a855f7', '#06b6d4', '#64748b']

function ChartSkeleton({ height }: { height: number }) {
  return (
    <div className="flex flex-col justify-end gap-2 pb-2" style={{ height }}>
      {[65, 90, 40, 75, 55, 30].map((w, i) => (
        <div key={i} className="h-5 bg-bg-raised animate-pulse rounded-sm" style={{ width: `${w}%` }} />
      ))}
    </div>
  )
}

export function OverviewPage() {
  const { data: summary, error: summaryErr, isLoading: summaryLoading } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
  })

  const { data: records, error: recordsErr } = useQuery({
    queryKey: ['records', { limit: 20 }],
    queryFn: () => api.getRecords({ limit: 20 }),
  })

  const { data: files } = useQuery({
    queryKey: ['files'],
    queryFn: api.listFiles,
  })

  const severityData = summary
    ? Object.entries(summary.severity_breakdown)
        .map(([k, v]) => ({ name: k || 'null', value: v }))
        .sort((a, b) => b.value - a.value)
    : []

  const eventData = summary
    ? Object.entries(summary.event_type_breakdown)
        .map(([k, v]) => ({ name: k || 'null', value: v }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 7)
    : []

  const toolData = summary
    ? Object.entries(summary.tool_breakdown)
        .map(([k, v]) => ({ name: k || 'unknown', value: v }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 8)
    : []

  const recentFiles = (files ?? []).slice(0, 6)

  return (
    <div className="space-y-4">
      {(summaryErr || recordsErr) && <ErrorBanner message="Could not load overview data." />}

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-3">
        <KpiCard label="Total Records"  value={summary?.total_records ?? '—'} accent="blue" />
        <KpiCard label="Files Ingested" value={summary?.total_files ?? '—'} accent="green" />
        <KpiCard label="Anomalies"      value={summary?.total_anomalies ?? '—'} accent="red" />
        <KpiCard
          label="Avg Confidence"
          value={summary ? formatConfidence(summary.avg_confidence) : '—'}
          accent="amber"
        />
      </div>

      {/* Charts row — 3 columns */}
      <div className="grid grid-cols-3 gap-3">
        {/* Severity distribution */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Severity Distribution</p>
          {summaryLoading ? <ChartSkeleton height={200} /> : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={severityData} barSize={22}>
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip contentStyle={{ background: '#1e2028', border: '1px solid #2a2f3a', color: '#e2e8f0', fontSize: 11, borderRadius: '4px' }} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                  {severityData.map((entry) => {
                    const key = entry.name.toUpperCase()
                    const fill = SEVERITY_COLOR[key] ?? '#64748b'
                    return <Cell key={entry.name} fill={fill} />
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Event types donut */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Event Types</p>
          {summaryLoading ? <ChartSkeleton height={200} /> : eventData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={eventData} dataKey="value" nameKey="name" cx="50%" cy="45%" outerRadius={68} innerRadius={36}>
                  {eventData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e2028', border: '1px solid #2a2f3a', color: '#e2e8f0', fontSize: 11, borderRadius: '4px' }} />
                <Legend wrapperStyle={{ fontSize: 10, color: '#64748b' }} iconSize={8} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center">
              <p className="text-text-muted text-xs">No event data yet</p>
            </div>
          )}
        </div>

        {/* Records by tool */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Records by Tool</p>
          {summaryLoading ? <ChartSkeleton height={200} /> : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={toolData} layout="vertical" barSize={12}>
                <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} width={64} />
                <Tooltip contentStyle={{ background: '#1e2028', border: '1px solid #2a2f3a', color: '#e2e8f0', fontSize: 11, borderRadius: '4px' }} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottom row — events feed + files panel */}
      <div className="grid grid-cols-3 gap-3">
        {/* Recent events — spans 2 cols */}
        <div className="col-span-2 bg-bg-panel border border-border">
          <div className="px-4 py-2.5 border-b border-border bg-bg-raised flex items-center justify-between">
            <p className="text-text-muted text-[11px] uppercase tracking-wider">Recent Events</p>
            <span className="text-text-muted text-[11px]">{records ? `${records.length} shown` : ''}</span>
          </div>
          <div className="divide-y divide-border">
            {(records ?? []).map(rec => (
              <div key={rec.id} className="flex items-center gap-3 px-4 py-2 text-sm hover:bg-bg-raised transition-colors">
                <span className="text-text-muted text-[11px] w-32 shrink-0 font-mono tabular-nums">
                  {formatTimestamp(rec.timestamp)}
                </span>
                <span className="text-text-muted w-20 shrink-0 truncate text-[11px]">{rec.tool_id ?? '—'}</span>
                <span className="text-text-primary flex-1 truncate text-[13px]">{rec.event_type ?? rec.raw_content?.slice(0, 50) ?? '—'}</span>
                <FormatBadge value={rec.source_format} />
                <SeverityBadge value={rec.severity} />
              </div>
            ))}
            {records !== undefined && records.length === 0 && (
              <div className="px-4 py-10 text-center">
                <p className="text-text-muted text-sm">No records yet.</p>
                <p className="text-text-muted text-xs mt-1">Upload a log file to get started.</p>
              </div>
            )}
          </div>
        </div>

        {/* Ingested files panel */}
        <div className="bg-bg-panel border border-border">
          <div className="px-4 py-2.5 border-b border-border bg-bg-raised">
            <p className="text-text-muted text-[11px] uppercase tracking-wider">Ingested Files</p>
          </div>
          <div className="divide-y divide-border">
            {recentFiles.length > 0 ? recentFiles.map(f => (
              <div key={f.id} className="px-4 py-2.5 hover:bg-bg-raised transition-colors">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-text-primary text-xs font-medium truncate flex-1">{f.filename}</span>
                  <FormatBadge value={f.format_detected} />
                </div>
                <div className="flex items-center gap-3 text-[11px] text-text-muted">
                  <span>{f.total_records.toLocaleString()} records</span>
                  <span className="text-border">·</span>
                  <span>{formatConfidence(f.avg_confidence)}</span>
                  <span className="text-border">·</span>
                  <span>{formatMs(f.parse_time_ms)}</span>
                </div>
              </div>
            )) : (
              <div className="px-4 py-10 text-center">
                <p className="text-text-muted text-xs">No files ingested yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
