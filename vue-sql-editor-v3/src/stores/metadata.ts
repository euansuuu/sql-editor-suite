import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DatabaseInfo, TableMetadata } from '../types'
import { getDatabases, getTables, getTableColumns } from '../api/metadata'

export const useMetadataStore = defineStore('metadata', () => {
  // 状态
  const databases = ref<DatabaseInfo[]>([])
  const currentDatasourceId = ref<string>('')
  const currentDatabase = ref<string>('')
  const currentTable = ref<TableMetadata | null>(null)
  const loading = ref(false)
  const expandedKeys = ref<string[]>([])

  // 计算属性
  const databaseNames = computed(() => databases.value.map(db => db.name))
  
  const currentDatabaseTables = computed(() => {
    const db = databases.value.find(d => d.name === currentDatabase.value)
    return db?.tables || []
  })

  // 获取数据库列表
  const fetchDatabases = async (datasourceId: string) => {
    if (!datasourceId) return
    
    loading.value = true
    currentDatasourceId.value = datasourceId
    
    try {
      const dbList = await getDatabases(datasourceId)
      databases.value = dbList.map(db => ({
        name: db.name,
        tables: []
      }))
    } catch (error) {
      console.error('Failed to fetch databases:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取数据库下的表列表
  const fetchTables = async (database: string, datasourceId?: string) => {
    const dsId = datasourceId || currentDatasourceId.value
    if (!dsId || !database) return

    loading.value = true
    currentDatabase.value = database
    
    try {
      const tables = await getTables(dsId, database)
      const dbIndex = databases.value.findIndex(d => d.name === database)
      if (dbIndex !== -1) {
        databases.value[dbIndex].tables = tables.map(t => ({
          name: t.name,
          type: (t.type || 'table') as 'table' | 'view',
          comment: t.comment || undefined,
          columns: [],
          partitions: []
        }))
      }
      // 展开数据库节点
      if (!expandedKeys.value.includes(database)) {
        expandedKeys.value.push(database)
      }
    } catch (error) {
      console.error('Failed to fetch tables:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取表详情
  const fetchTableDetail = async (table: string, database?: string, datasourceId?: string) => {
    const dsId = datasourceId || currentDatasourceId.value
    const dbName = database || currentDatabase.value
    if (!dsId || !dbName || !table) return

    loading.value = true
    
    try {
      const columns = await getTableColumns(dsId, dbName, table)
      const tableDetail: TableMetadata = {
        name: table,
        type: 'table',
        columns,
        partitions: []
      }
      currentTable.value = tableDetail

      const dbIndex = databases.value.findIndex(d => d.name === dbName)
      if (dbIndex !== -1) {
        const tableIndex = databases.value[dbIndex].tables.findIndex(t => t.name === table)
        if (tableIndex !== -1) {
          databases.value[dbIndex].tables[tableIndex] = tableDetail
        }
      }
    } catch (error) {
      console.error('Failed to fetch table detail:', error)
    } finally {
      loading.value = false
    }
  }

  // 切换展开状态
  const toggleExpand = (key: string) => {
    const index = expandedKeys.value.indexOf(key)
    if (index === -1) {
      expandedKeys.value.push(key)
    } else {
      expandedKeys.value.splice(index, 1)
    }
  }

  // 设置当前数据库
  const setCurrentDatabase = (database: string) => {
    currentDatabase.value = database
  }

  // 清除元数据缓存
  const clearMetadata = () => {
    databases.value = []
    currentDatabase.value = ''
    currentTable.value = null
    expandedKeys.value = []
  }

  return {
    databases,
    currentDatasourceId,
    currentDatabase,
    currentTable,
    loading,
    expandedKeys,
    databaseNames,
    currentDatabaseTables,
    fetchDatabases,
    fetchTables,
    fetchTableDetail,
    toggleExpand,
    setCurrentDatabase,
    clearMetadata
  }
})
