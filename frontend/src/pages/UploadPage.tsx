import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Upload, FileCheck, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'
import type { UploadResponse } from '@/lib/api'
import { FormatBadge } from '@/components/shared/FormatBadge'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { formatMs, formatConfidence } from '@/lib/utils'

export function UploadPage() {
  const qc = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const uploadCounter = useRef(0)
  const [results, setResults] = useState<Array<UploadResponse & { _key: number }>>([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const { data: samples = [] } = useQuery({
    queryKey: ['samples'],
    queryFn: api.listSamples,
  })

  async function handleFiles(files: FileList | File[]) {
    setUploading(true)
    setError(null)
    const arr = Array.from(files)
    const newResults: Array<UploadResponse & { _key: number }> = []
    const errors: string[] = []
    for (const file of arr) {
      try {
        const res = await api.uploadFile(file)
        newResults.push({ ...res, _key: uploadCounter.current++ })
      } catch {
        errors.push(`Failed to upload "${file.name}"`)
      }
    }
    if (errors.length > 0) {
      setError(errors.length === 1 ? errors[0] : `${errors.length} files failed to upload`)
    }
    if (newResults.length > 0) {
      setResults(prev => [...newResults, ...prev])
      qc.invalidateQueries()
    }
    setUploading(false)
  }

  async function handleSample(name: string) {
    setUploading(true)
    setError(null)
    try {
      const res = await api.uploadSample(name)
      setResults(prev => [{ ...res, _key: uploadCounter.current++ }, ...prev])
      qc.invalidateQueries()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(`Failed to load sample "${name}": ${msg}`)
    }
    setUploading(false)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {error && <ErrorBanner message={error} />}

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files) }}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded cursor-pointer flex flex-col items-center justify-center py-14 transition-colors ${
          dragOver ? 'border-accent-blue bg-accent-blue/5' : 'border-border hover:border-accent-blue/50 hover:bg-bg-panel'
        }`}
      >
        <Upload className="w-8 h-8 text-text-muted mb-3" />
        <p className="text-text-primary font-medium">Drop log files here or click to browse</p>
        <p className="text-text-muted text-sm mt-1">JSON, XML, CSV, Syslog, Key-Value, Text, Binary, Parquet</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={e => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {uploading && (
        <div className="flex items-center gap-3 text-text-muted text-sm">
          <div className="w-4 h-4 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
          Parsing...
        </div>
      )}

      {/* Sample logs */}
      <div>
        <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Quick Demo — Sample Logs</p>
        <div className="flex flex-wrap gap-2">
          {samples.filter(n => !n.endsWith('.py')).map(name => (
            <Button
              key={name}
              variant="outline"
              size="sm"
              disabled={uploading}
              onClick={() => handleSample(name)}
              className="bg-bg-panel border-border text-text-muted hover:text-text-primary hover:bg-bg-raised text-xs font-mono"
            >
              {name}
            </Button>
          ))}
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div>
          <p className="text-text-muted text-[11px] uppercase tracking-wider mb-3">Parse Results</p>
          <div className="space-y-3">
            {results.map((r) => (
              <div key={r._key} className="bg-bg-panel border border-border p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <FileCheck className="w-4 h-4 text-accent-green shrink-0" />
                  <span className="text-text-primary font-medium flex-1 truncate">{r.filename}</span>
                  <FormatBadge value={r.format_detected} />
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Records</p>
                    <p className="text-text-primary font-semibold tabular-nums">{r.total_records}</p>
                  </div>
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Anomalies</p>
                    <p className={`font-semibold tabular-nums ${r.anomalies_found > 0 ? 'text-accent-red' : 'text-text-muted'}`}>
                      {r.anomalies_found}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Parse Time</p>
                    <p className="text-text-primary font-semibold">{formatMs(r.parse_time_ms)}</p>
                  </div>
                  <div>
                    <p className="text-text-muted text-xs mb-0.5">Confidence</p>
                    <p className="text-text-primary font-semibold">{formatConfidence(r.avg_confidence)}</p>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-text-muted">
                    <span>Confidence</span>
                    <span>{formatConfidence(r.avg_confidence)}</span>
                  </div>
                  <Progress
                    value={r.avg_confidence * 100}
                    className="h-1.5 bg-bg-raised [&>div]:bg-accent-blue"
                  />
                </div>
                {r.anomalies_found > 0 && (
                  <div className="flex items-center gap-2 text-accent-amber text-xs">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    {r.anomalies_found} anomal{r.anomalies_found === 1 ? 'y' : 'ies'} detected
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
