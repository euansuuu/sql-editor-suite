import { request } from './request'
import type { QueryResult, ColumnInfo, PaginationParams, PaginatedResult } from '../types'

interface ExecuteResultResponse {
  query_id: string
}

interface QueryStatusResponse {
  id: string
  datasource_id: number
  status: string
  sql: string
  error_message: string | null
  execution_time: number | null
  row_count: number | null
  created_at: string
  updated_at: string
}

interface QueryResultResponse {
  id: string
  status: string
  columns: ColumnInfo[]
  data: any[][]
  has_more: boolean
  total_rows: number
  error?: string
}

export const executeQuery = (data: {
  datasourceId: string
  database: string
  sql: string
  maxRows?: number
}) => {
  return request.post<ExecuteResultResponse>('/query/execute', data)
}

export const cancelQuery = (queryId: string) => {
  return request.post<void>(`/query/${queryId}/cancel`)
}

export const getQueryResult = (queryId: string, params?: PaginationParams) => {
  return request.get<QueryResultResponse>(`/query/${queryId}/result`, params)
}

export const getQueryHistory = (params: PaginationParams & { datasourceId?: string; keyword?: string }) => {
  return request.get<PaginatedResult<QueryResult>>('/query/history', params)
}

export const exportQueryResult = (queryId: string, format: 'csv' | 'excel') => {
  return request.get<Blob>(`/query/${queryId}/export`, { format }, {
    responseType: 'blob'
  })
}

export const getQueryStatus = (queryId: string) => {
  return request.get<QueryStatusResponse>(`/query/${queryId}/status`)
}

export function transformQueryResult(raw: QueryResultResponse, baseResult: Partial<QueryResult>): QueryResult {
  const columns = raw.columns || []
  const rows = (raw.data || []).map(row => {
    const obj: Record<string, any> = {}
    columns.forEach((col, i) => {
      obj[col.name] = row[i]
    })
    return obj
  })

  return {
    id: raw.id || baseResult.id || '',
    sql: baseResult.sql || '',
    datasourceId: baseResult.datasourceId || '',
    database: baseResult.database || '',
    status: 'success',
    columns,
    rows,
    executionTime: baseResult.executionTime,
    endTime: Date.now(),
    affectedRows: raw.total_rows,
  }
}
