import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, X } from 'lucide-react'
import { api } from '@/lib/api'
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
    tool_id:       toolId   || undefined,
    severity:      severity || undefined,
    source_format: format   || undefined,
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
                  {(() => {
                    const params = parseParams(rec.parameters_json)
                    return Object.keys(params).length > 0 && (
                      <div>
                        <p className="text-text-muted mb-1 uppercase tracking-wider">Parameters</p>
                        <pre className="bg-bg-raised border border-border rounded p-3 text-text-primary font-mono overflow-x-auto">
                          {JSON.stringify(params, null, 2)}
                        </pre>
                      </div>
                    )
                  })()}
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
          {records.length === 0 && !isFetching && (
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
              className={`px-2 py-0.5 rounded cursor-pointer ${limit === s ? 'bg-accent-blue/20 text-accent-blue' : 'hover:bg-bg-raised text-text-muted'}`}
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
            {records.length === 0 ? '0 results' : `${offset + 1}–${offset + records.length}`}
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
