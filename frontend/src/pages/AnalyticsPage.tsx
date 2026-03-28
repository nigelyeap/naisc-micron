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
                {severityData.map((e) => {
                  const u = e.name.toUpperCase()
                  const fill = u.includes('CRIT') ? '#ef4444' : u.includes('WARN') ? '#f59e0b' : u.includes('INFO') ? '#3b82f6' : '#64748b'
                  return <Cell key={e.name} fill={fill} />
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
                {eventData.map((e, i) => <Cell key={e.name} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
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
