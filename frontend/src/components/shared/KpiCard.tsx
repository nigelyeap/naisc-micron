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
    <div className={`bg-bg-panel border-l-2 ${accentBorder[accent]} px-4 py-3 transition-all duration-200 hover:bg-bg-raised hover:shadow-lg group cursor-default`}>
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
