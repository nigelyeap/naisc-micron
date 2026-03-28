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


export function OverviewPage() {
  const { data: summary, error: summaryErr, isLoading: summaryLoading } = useQuery({
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

  const toolData = summary
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
          {summaryLoading ? (
            <div className="h-[180px] flex flex-col justify-end gap-2 pb-2">
              {[65, 90, 40, 75, 55, 30].map((w, i) => (
                <div key={i} className="h-5 bg-bg-raised animate-pulse rounded-sm" style={{ width: `${w}%` }} />
              ))}
            </div>
          ) : (
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
                  return <Cell key={entry.name} fill={fill} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          )}
        </div>

        {/* Tool breakdown */}
        <div className="bg-bg-panel border border-border p-4">
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-4">Records by Tool</p>
          {summaryLoading ? (
            <div className="h-[180px] flex flex-col justify-end gap-2 pb-2">
              {[65, 90, 40, 75, 55, 30].map((w, i) => (
                <div key={i} className="h-5 bg-bg-raised animate-pulse rounded-sm" style={{ width: `${w}%` }} />
              ))}
            </div>
          ) : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={toolData} layout="vertical" barSize={14}>
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
              <Tooltip
                contentStyle={{ background: '#1e2028', border: '1px solid #1e2028', color: '#e2e8f0', fontSize: 12 }}
                cursor={{ fill: '#1e2028' }}
              />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
          )}
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
          {records !== undefined && records.length === 0 && (
            <p className="px-4 py-6 text-text-muted text-sm text-center">No records yet. Upload a log file to get started.</p>
          )}
        </div>
      </div>
    </div>
  )
}
