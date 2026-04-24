import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DataSource } from '../types'
import { getDatasourceList, createDatasource, updateDatasource, deleteDatasource, testDatasourceConnection } from '../api/datasource'

export const useDatasourceStore = defineStore('datasource', () => {
  // 状态
  const datasources = ref<DataSource[]>([])
  const currentDatasource = ref<DataSource | null>(null)
  const loading = ref(false)

  // 计算属性
  const datasourceOptions = computed(() => {
    return datasources.value.map(ds => ({
      label: ds.name,
      value: ds.id
    }))
  })

  // 获取数据源列表
  const fetchDatasources = async () => {
    loading.value = true
    try {
      const result = await getDatasourceList({ page: 1, pageSize: 100 })
      datasources.value = result.list
    } catch (error) {
      console.error('Failed to fetch datasources:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取数据源详情
  const fetchDatasourceDetail = async (id: string) => {
    loading.value = true
    try {
      const datasource = await getDatasourceList({ page: 1, pageSize: 100 })
      currentDatasource.value = datasource.list.find(d => d.id === id) || null
    } catch (error) {
      console.error('Failed to fetch datasource detail:', error)
    } finally {
      loading.value = false
    }
  }

  // 创建数据源
  const addDatasource = async (data: Omit<DataSource, 'id' | 'createdAt' | 'updatedAt'>) => {
    loading.value = true
    try {
      const newDatasource = await createDatasource(data)
      datasources.value.push(newDatasource)
      return newDatasource
    } finally {
      loading.value = false
    }
  }

  // 更新数据源
  const editDatasource = async (id: string, data: Partial<DataSource>) => {
    loading.value = true
    try {
      const updated = await updateDatasource(id, data)
      const index = datasources.value.findIndex(d => d.id === id)
      if (index !== -1) {
        datasources.value[index] = updated
      }
      if (currentDatasource.value?.id === id) {
        currentDatasource.value = updated
      }
      return updated
    } finally {
      loading.value = false
    }
  }

  // 删除数据源
  const removeDatasource = async (id: string) => {
    loading.value = true
    try {
      await deleteDatasource(id)
      datasources.value = datasources.value.filter(d => d.id !== id)
      if (currentDatasource.value?.id === id) {
        currentDatasource.value = null
      }
    } finally {
      loading.value = false
    }
  }

  // 测试连接
  const testConnection = async (data: Partial<DataSource>) => {
    try {
      return await testDatasourceConnection(data)
    } catch (error) {
      return { success: false, message: (error as Error).message }
    }
  }

  // 设置当前数据源
  const setCurrentDatasource = (datasource: DataSource | null) => {
    currentDatasource.value = datasource
  }

  return {
    datasources,
    currentDatasource,
    loading,
    datasourceOptions,
    fetchDatasources,
    fetchDatasourceDetail,
    addDatasource,
    editDatasource,
    removeDatasource,
    testConnection,
    setCurrentDatasource
  }
})
