interface FormatBadgeProps { value: string | null }

export function FormatBadge({ value }: FormatBadgeProps) {
  if (!value) return <span className="text-text-muted text-xs">—</span>
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded bg-bg-raised text-text-muted text-[13px] font-mono uppercase tracking-wide">
      {value}
    </span>
  )
}
