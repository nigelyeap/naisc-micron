import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

http.interceptors.response.use(
  r => r,
  err => {
    const detail = err?.response?.data?.detail
    if (detail) err.message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    return Promise.reject(err)
  }
)

// ---- Types -----------------------------------------------------------------

export interface LogFile {
  id: number
  filename: string
  format_detected: string | null
  upload_time: string
  total_records: number
  avg_confidence: number
  parse_time_ms: number
}

export interface LogRecord {
  id: number
  file_id: number
  source_format: string
  timestamp: string | null
  tool_id: string | null
  module_id: string | null
  event_type: string | null
  severity: string | null
  parameters_json: string | null
  raw_content: string | null
  confidence: number
  parse_warnings_json: string | null
}

export interface Anomaly {
  id: number
  record_id: number | string
  parameter: string
  value: number
  expected_min: number
  expected_max: number
  anomaly_type: string
  severity: string
  z_score: number
  description: string
  detected_at: string
}

export interface UploadResponse {
  file_id: number
  filename: string
  format_detected: string | null
  total_records: number
  avg_confidence: number
  parse_time_ms: number
  anomalies_found: number
}

export interface SummaryStats {
  total_files: number
  total_records: number
  total_anomalies: number
  avg_confidence: number
  event_type_breakdown: Record<string, number>
  severity_breakdown: Record<string, number>
  tool_breakdown: Record<string, number>
}

export interface TimeseriesPoint {
  record_id: number
  timestamp: string
  tool_id: string
  parameter: string
  value: number
}

export interface TimeseriesResponse {
  parameter: string
  tool_id: string | null
  data: TimeseriesPoint[]
}

export interface NLQueryResponse {
  generated_sql: string
  results: Record<string, unknown>[]
  explanation: string
  confidence: number
}

export interface HealthResponse {
  status: string
  database: string
  parser_available: boolean
  analytics_available: boolean
  nl_query_mode: string
}

export interface RecordFilters {
  tool_id?: string
  event_type?: string
  severity?: string
  file_id?: number
  limit?: number
  offset?: number
  start_date?: string
  end_date?: string
}

// ---- API functions ---------------------------------------------------------

export const api = {
  health: () =>
    http.get<HealthResponse>('/health').then(r => r.data),

  uploadFile: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post<UploadResponse>('/upload', fd).then(r => r.data)
  },

  uploadSample: (filename: string) =>
    http.post<UploadResponse>(`/samples/upload/${encodeURIComponent(filename)}`).then(r => r.data),

  listSamples: () =>
    http.get<string[]>('/samples').then(r => r.data),

  listFiles: () =>
    http.get<LogFile[]>('/files').then(r => r.data),

  getRecords: (filters: RecordFilters = {}) =>
    http.get<LogRecord[]>('/records', { params: filters }).then(r => r.data),

  getRecord: (id: number) =>
    http.get<LogRecord>(`/records/${id}`).then(r => r.data),

  getAnomalies: () =>
    http.get<Anomaly[]>('/anomalies').then(r => r.data),

  getSummary: () =>
    http.get<SummaryStats>('/analytics/summary').then(r => r.data),

  getTimeseries: (parameter: string, tool_id?: string) =>
    http.get<TimeseriesResponse>('/analytics/timeseries', {
      params: { parameter, tool_id },
    }).then(r => r.data),

  nlQuery: (question: string) =>
    http.post<NLQueryResponse>('/query', { question }).then(r => r.data),
}
