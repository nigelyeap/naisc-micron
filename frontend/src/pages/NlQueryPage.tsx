import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '@/lib/api'
import type { NLQueryResponse } from '@/lib/api'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

const PRESETS = [
  'Show me all alarm events',
  'What is the average temperature per tool?',
  'Show the most recent anomalies',
  'How many records were parsed per file format?',
]

export function NlQueryPage() {
  const [question, setQuestion] = useState('')
  const [sqlOpen, setSqlOpen]   = useState(false)
  const [result, setResult]     = useState<NLQueryResponse | null>(null)

  const { mutate, isPending, error } = useMutation({
    mutationFn: (q: string) => api.nlQuery(q),
    onSuccess: data => { setResult(data); setSqlOpen(false) },
  })

  function submit() {
    if (!question.trim()) return
    mutate(question.trim())
  }

  const columns = result?.results[0] ? Object.keys(result.results[0]) : []

  return (
    <div className="space-y-5 max-w-2xl">
      {/* Preset chips */}
      <div>
        <p className="text-text-muted text-[11px] uppercase tracking-wider mb-2">Example queries</p>
        <div className="flex flex-wrap gap-2">
          {PRESETS.map(p => (
            <button
              key={p}
              onClick={() => setQuestion(p)}
              className="text-xs bg-bg-panel border border-border text-text-muted hover:text-text-primary hover:border-accent-blue/50 px-3 py-1.5 rounded transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <Textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask anything about your log data in plain English..."
          rows={3}
          className="bg-bg-panel border-border text-text-primary placeholder:text-text-muted resize-none focus:border-accent-blue"
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit() }}
        />
        <div className="flex items-center justify-between">
          <p className="text-text-muted text-xs">Cmd/Ctrl + Enter to submit</p>
          <Button
            onClick={submit}
            disabled={isPending || !question.trim()}
            size="sm"
            className="bg-accent-blue hover:bg-blue-500 text-white"
          >
            {isPending
              ? <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              : <Send className="w-3.5 h-3.5 mr-2" />}
            Query
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message="Query failed. Is the API running?" />}

      {result && (
        <div className="space-y-4">
          {/* Explanation */}
          {result.explanation && (
            <p className="text-text-muted text-sm">{result.explanation}</p>
          )}

          {/* SQL collapsible */}
          <div className="bg-bg-panel border border-border rounded overflow-hidden">
            <button
              onClick={() => setSqlOpen(o => !o)}
              className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-text-muted hover:bg-bg-raised transition-colors"
            >
              <span className="uppercase tracking-wider">Generated SQL</span>
              {sqlOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            {sqlOpen && (
              <pre className="px-4 py-3 border-t border-border text-xs font-mono text-accent-green bg-bg-base overflow-x-auto">
                {result.generated_sql}
              </pre>
            )}
          </div>

          {/* Results table */}
          {result.results.length > 0 ? (
            <div className="bg-bg-panel border border-border overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg-raised border-b border-border">
                    {columns.map(c => (
                      <th key={c} className="text-left px-3 py-2 text-[11px] text-text-muted uppercase tracking-wider font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {result.results.map((row, i) => (
                    <tr key={i} className="hover:bg-bg-raised transition-colors">
                      {columns.map(c => (
                        <td key={c} className="px-3 py-2 text-text-primary font-mono text-xs">
                          {String(row[c] ?? '—')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-text-muted text-sm text-center py-6 bg-bg-panel border border-border">
              Query returned no results.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
