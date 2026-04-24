// SQL 方言类型
export type SQLDialect = 'hive' | 'impala' | 'spark' | 'mysql' | 'postgresql' | 'trino'

// 数据源类型
export interface DataSource {
  id: string
  name: string
  type: SQLDialect
  host: string
  port: number
  database: string
  username?: string
  password?: string
  authType: 'basic' | 'kerberos'
  kerberos?: {
    principal: string
    keytabPath?: string
  }
  createdAt: string
  updatedAt: string
}

// 查询状态
export type QueryStatus = 'idle' | 'running' | 'success' | 'failed'

// 查询执行结果
export interface QueryResult {
  id: string
  sql: string
  datasourceId: string
  database: string
  status: QueryStatus
  startTime?: number
  endTime?: number
  executionTime?: number
  columns?: ColumnInfo[]
  rows?: Record<string, any>[]
  error?: string
  affectedRows?: number
}

// 列信息
export interface ColumnInfo {
  name: string
  type: string
  comment?: string
}

// 表元数据
export interface TableMetadata {
  name: string
  type: 'table' | 'view'
  comment?: string
  columns: ColumnInfo[]
  partitions?: ColumnInfo[]
  rowCount?: number
  size?: number
}

// 数据库信息
export interface DatabaseInfo {
  name: string
  tables: TableMetadata[]
}

// 标签页状态
export interface TabState {
  id: string
  title: string
  sql: string
  cursorPosition: { line: number; column: number }
  datasourceId?: string
  database?: string
  result?: QueryResult
  history: QueryResult[]
  isModified: boolean
}

// API 响应通用结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页参数
export interface PaginationParams {
  page: number
  pageSize: number
}

// 分页结果
export interface PaginatedResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}
