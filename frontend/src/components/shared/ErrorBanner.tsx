import { AlertCircle } from 'lucide-react'

interface ErrorBannerProps { message?: string }

export function ErrorBanner({ message = 'Failed to load data.' }: ErrorBannerProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded text-accent-red text-sm">
      <AlertCircle className="w-4 h-4 shrink-0" />
      {message}
    </div>
  )
}
