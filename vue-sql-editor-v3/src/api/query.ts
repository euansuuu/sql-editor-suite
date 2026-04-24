import { request } from './request'
import type { QueryResult, PaginationParams, PaginatedResult } from '../types'

// 执行 SQL 查询
export const executeQuery = (data: {
  datasourceId: string
  database: string
  sql: string
  maxRows?: number
}) => {
  return request.post<QueryResult>('/query/execute', data)
}

// 取消查询
export const cancelQuery = (queryId: string) => {
  return request.post<void>(`/query/${queryId}/cancel`)
}

// 获取查询结果
export const getQueryResult = (queryId: string, params?: PaginationParams) => {
  return request.get<QueryResult>(`/query/${queryId}/result`, params)
}

// 获取查询历史
export const getQueryHistory = (params: PaginationParams & { datasourceId?: string; keyword?: string }) => {
  return request.get<PaginatedResult<QueryResult>>('/query/history', params)
}

// 导出查询结果
export const exportQueryResult = (queryId: string, format: 'csv' | 'excel') => {
  return request.get<Blob>(`/query/${queryId}/export`, { format }, {
    responseType: 'blob'
  })
}

// 获取查询状态
export const getQueryStatus = (queryId: string) => {
  return request.get<{ status: string; progress: number }>(`/query/${queryId}/status`)
}
