import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface TopBarProps { title: string }

export function TopBar({ title }: TopBarProps) {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30_000,
    retry: false,
  })

  const { data: files, isLoading: filesLoading } = useQuery({
    queryKey: ['files'],
    queryFn: api.listFiles,
    refetchInterval: 10_000,
    retry: false,
  })

  const connected = health?.status === 'ok'

  return (
    <header className="h-12 border-b border-border bg-bg-base flex items-center px-5 shrink-0">
      <h1 className="text-text-primary text-base font-semibold tracking-tight flex-1">{title}</h1>
      <div className="flex items-center gap-4 text-xs text-text-muted">
        {!filesLoading && files !== undefined && (
          <span>{files.length} file{files.length !== 1 ? 's' : ''} loaded</span>
        )}
        {!healthLoading && (
          <div className="flex items-center gap-1.5">
            {connected ? (
              <div className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-green opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-green" />
              </div>
            ) : (
              <div className="w-2 h-2 rounded-full bg-accent-red" />
            )}
            <span>{connected ? 'API connected' : 'API unavailable'}</span>
          </div>
        )}
      </div>
    </header>
  )
}
