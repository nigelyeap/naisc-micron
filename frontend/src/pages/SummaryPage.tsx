import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { api } from '@/lib/api'
import type { SummaryStats } from '@/lib/api'
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

  const { data: summary, error, isFetching } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
    enabled: generated,
  })

  function generate() {
    setGenerated(true)
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
