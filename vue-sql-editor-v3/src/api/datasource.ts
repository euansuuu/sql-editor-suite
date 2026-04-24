import { request } from './request'
import type { DataSource, ApiResponse, PaginatedResult, PaginationParams } from '../types'

// 获取数据源列表
export const getDatasourceList = (params?: PaginationParams & { keyword?: string }) => {
  return request.get<PaginatedResult<DataSource>>('/datasources', params)
}

// 获取数据源详情
export const getDatasourceDetail = (id: string) => {
  return request.get<DataSource>(`/datasources/${id}`)
}

// 创建数据源
export const createDatasource = (data: Omit<DataSource, 'id' | 'createdAt' | 'updatedAt'>) => {
  return request.post<DataSource>('/datasources', data)
}

// 更新数据源
export const updateDatasource = (id: string, data: Partial<DataSource>) => {
  return request.put<DataSource>(`/datasources/${id}`, data)
}

// 删除数据源
export const deleteDatasource = (id: string) => {
  return request.delete<void>(`/datasources/${id}`)
}

// 测试数据源连接
export const testDatasourceConnection = (data: Partial<DataSource>) => {
  return request.post<{ success: boolean; message?: string }>('/datasources/test', data)
}

// 上传 Keytab 文件
export const uploadKeytab = (principal: string, file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.upload<{ path: string; filename: string }>(`/kerberos/keytab/upload?principal=${encodeURIComponent(principal)}`, formData, onProgress)
}
