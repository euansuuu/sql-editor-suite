import { request } from './request'
import type { DatabaseInfo, TableMetadata, ColumnInfo } from '../types'

// 获取数据库列表
export const getDatabases = (datasourceId: string) => {
  return request.get<string[]>(`/metadata/${datasourceId}/databases`)
}

// 获取数据库下的表列表
export const getTables = (datasourceId: string, database: string) => {
  return request.get<Array<{ name: string; type: string; comment?: string }>>(
    `/metadata/${datasourceId}/databases/${database}/tables`
  )
}

// 获取表详情
export const getTableDetail = (datasourceId: string, database: string, table: string) => {
  return request.get<TableMetadata>(
    `/metadata/${datasourceId}/databases/${database}/tables/${table}`
  )
}

// 获取表的列信息
export const getTableColumns = (datasourceId: string, database: string, table: string) => {
  return request.get<ColumnInfo[]>(
    `/metadata/${datasourceId}/databases/${database}/tables/${table}/columns`
  )
}

// 获取表分区信息
export const getTablePartitions = (datasourceId: string, database: string, table: string) => {
  return request.get<ColumnInfo[]>(
    `/metadata/${datasourceId}/databases/${database}/tables/${table}/partitions`
  )
}

// 获取表预览数据
export const getTablePreview = (datasourceId: string, database: string, table: string, limit = 100) => {
  return request.get<{ columns: ColumnInfo[]; rows: Record<string, any>[] }>(
    `/metadata/${datasourceId}/databases/${database}/tables/${table}/preview`,
    { limit }
  )
}

// 刷新元数据缓存
export const refreshMetadata = (datasourceId: string, database?: string, table?: string) => {
  return request.post<void>(`/metadata/${datasourceId}/refresh`, { database, table })
}
