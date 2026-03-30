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
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[13px] font-semibold tracking-wide ${cls}`}>
      {norm}
    </span>
  )
}
