const STAGES = [
  {
    id: 'input',
    label: 'Raw Log Files',
    color: '#64748b',
    sub: ['JSON', 'XML', 'CSV', 'Syslog', 'KV', 'Text', 'Binary'],
    desc: 'Semiconductor equipment logs from diverse vendors in 7 formats',
  },
  {
    id: 'detector',
    label: 'Format Detector',
    color: '#a855f7',
    sub: ['Byte patterns', 'Regex heuristics', 'Statistical analysis'],
    desc: 'Content-based detection — no file extension required',
  },
  {
    id: 'parser',
    label: 'Parser',
    color: '#3b82f6',
    sub: ['JSONParser', 'XMLParser', 'CSVParser', 'SyslogParser', 'KVParser', 'TextParser', 'BinaryParser'],
    desc: 'Per-format parsers with recursive flattening and LLM fallback',
  },
  {
    id: 'schema',
    label: 'Schema Inferencer',
    color: '#06b6d4',
    sub: ['Field mapping', 'Vendor normalisation'],
    desc: 'Maps vendor-specific fields to the unified semiconductor schema',
  },
  {
    id: 'normaliser',
    label: 'Normalizer',
    color: '#22c55e',
    sub: ['UnifiedLogRecord', 'Timestamp', 'Severity', 'Parameters'],
    desc: 'Produces consistent UnifiedLogRecord instances for all formats',
  },
  {
    id: 'db',
    label: 'SQLite DB',
    color: '#f59e0b',
    sub: ['log_files', 'log_records', 'anomalies'],
    desc: 'WAL-mode SQLite with thread-safe connections',
  },
  {
    id: 'api',
    label: 'FastAPI',
    color: '#ef4444',
    sub: ['11 endpoints', 'NL → SQL', 'Anomaly detection'],
    desc: 'REST API with Claude-powered natural language queries',
  },
  {
    id: 'ui',
    label: 'React UI',
    color: '#3b82f6',
    sub: ['Overview', 'Explorer', 'Analytics', 'NL Query', 'Summary'],
    desc: 'This dashboard — Vite + shadcn/ui + Recharts',
  },
]

const COMPONENTS: [string, string, string][] = [
  ['Format Detector',   'parser/format_detector.py',          'Content-based format identification'],
  ['Parser Pipeline',   'parser/pipeline.py',                 'Orchestrates detect → parse → normalize'],
  ['JSON Parser',       'parser/parsers/json_parser.py',       'Recursive nested JSON flattening'],
  ['XML Parser',        'parser/parsers/xml_parser.py',        'ElementTree-based extraction'],
  ['CSV Parser',        'parser/parsers/csv_parser.py',        'Standard CSV with header inference'],
  ['Syslog Parser',     'parser/parsers/syslog_parser.py',     'RFC 3164/5424 parsing'],
  ['KV Parser',         'parser/parsers/kv_parser.py',         'Key=value regex extraction'],
  ['Text Parser',       'parser/parsers/text_parser.py',       'Unstructured text pattern matching'],
  ['Binary Parser',     'parser/parsers/binary_parser.py',     'Hex dump + embedded string extraction'],
  ['LLM Fallback',      'parser/llm_fallback.py',              'Claude API for unknown formats'],
  ['Schema Inferencer', 'parser/schema_inferencer.py',         'Maps vendor fields to unified schema'],
  ['Normalizer',        'parser/normalizer.py',                'Produces UnifiedLogRecord instances'],
  ['Anomaly Detector',  'analytics/anomaly_detector.py',       'Z-score, IQR, rate-of-change detection'],
  ['Trend Analyzer',    'analytics/trend_analyzer.py',         'Linear regression + drift detection'],
  ['Fault Correlator',  'analytics/fault_correlator.py',       'Alarm-to-anomaly correlation'],
  ['Database',          'backend/database.py',                 'SQLite WAL-mode thread-safe wrapper'],
  ['NL Query Engine',   'backend/nl_query.py',                 'English → SQL via Claude API'],
  ['FastAPI App',       'backend/app.py',                      '11-endpoint REST API'],
  ['React Frontend',    'frontend/src/',                       'This dashboard'],
]

export function ArchitecturePage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-text-primary text-lg font-semibold mb-1">Pipeline Architecture</h2>
        <p className="text-text-muted text-sm">
          End-to-end flow from raw semiconductor equipment logs to queryable structured data.
        </p>
      </div>

      {/* Pipeline flow */}
      <div className="overflow-x-auto pb-4">
        <div className="flex items-start gap-0 min-w-max">
          {STAGES.map((stage, i) => (
            <div key={stage.id} className="flex items-center">
              {/* Stage box */}
              <div className="w-40 bg-bg-panel border border-border rounded p-3 flex flex-col gap-2">
                <div
                  className="text-xs font-semibold text-center py-1.5 px-2 rounded"
                  style={{ background: stage.color + '20', color: stage.color }}
                >
                  {stage.label}
                </div>
                <div className="flex flex-col gap-1">
                  {stage.sub.map(s => (
                    <div key={s} className="text-[10px] text-text-muted bg-bg-raised px-1.5 py-0.5 rounded font-mono">
                      {s}
                    </div>
                  ))}
                </div>
                <p className="text-[10px] text-text-muted leading-relaxed border-t border-border pt-2 mt-1">
                  {stage.desc}
                </p>
              </div>
              {/* Arrow */}
              {i < STAGES.length - 1 && (
                <div className="flex items-center mx-1 mt-6">
                  <div className="w-4 h-px bg-border" />
                  <div
                    className="w-0 h-0"
                    style={{
                      borderTop: '4px solid transparent',
                      borderBottom: '4px solid transparent',
                      borderLeft: '5px solid #1e2028',
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Component table */}
      <div className="bg-bg-panel border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-bg-raised">
          <p className="text-text-muted text-[11px] uppercase tracking-wider">Component Reference</p>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-2.5 text-[11px] text-text-muted uppercase tracking-wider font-medium">Component</th>
              <th className="text-left px-4 py-2.5 text-[11px] text-text-muted uppercase tracking-wider font-medium">File(s)</th>
              <th className="text-left px-4 py-2.5 text-[11px] text-text-muted uppercase tracking-wider font-medium">Responsibility</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {COMPONENTS.map(([comp, file, desc]) => (
              <tr key={comp} className="hover:bg-bg-raised transition-colors">
                <td className="px-4 py-2.5 text-text-primary font-medium">{comp}</td>
                <td className="px-4 py-2.5 text-accent-green font-mono text-xs">{file}</td>
                <td className="px-4 py-2.5 text-text-muted">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
