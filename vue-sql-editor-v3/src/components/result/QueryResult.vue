<template>
  <div class="query-result">
    <!-- 状态头部 -->
    <div class="result-header" v-if="result">
      <div class="status-info">
        <el-tag :type="statusType" size="small">
          {{ statusText }}
        </el-tag>
        <span v-if="result.executionTime !== undefined" class="execution-time">
          执行时间: {{ formatTime(result.executionTime) }}
        </span>
        <span v-if="result.rows" class="row-count">
          共 {{ result.rows.length }} 行
        </span>
        <span v-if="result.affectedRows !== undefined" class="affected-rows">
          影响行数: {{ result.affectedRows }}
        </span>
      </div>
      <div class="result-actions">
        <el-button v-if="result.status === 'success' && result.rows" size="small" @click="exportCsv">
          导出 CSV
        </el-button>
        <el-button v-if="result.status === 'success' && result.rows" size="small" @click="exportExcel">
          导出 Excel
        </el-button>
      </div>
    </div>

    <!-- 错误信息 -->
    <el-alert
      v-if="result?.status === 'failed' && result?.error"
      :title="result.error"
      type="error"
      :closable="false"
      show-icon
      class="error-alert"
    />

    <!-- 加载状态 -->
    <div v-if="result?.status === 'running'" class="loading-container">
      <el-icon class="is-loading" size="40"><Loading /></el-icon>
      <p>查询执行中...</p>
    </div>

    <!-- 结果表格 -->
    <div v-if="result?.status === 'success' && result.rows && result.columns" class="result-table-container">
      <el-table
        :data="paginatedRows"
        border
        size="small"
        :header-cell-style="{ background: '#f5f7fa' }"
        style="width: 100%"
      >
        <el-table-column
          v-for="column in result.columns"
          :key="column.name"
          :prop="column.name"
          :label="column.name"
          :min-width="120"
          show-overflow-tooltip
        >
          <template #header>
            <div class="column-header">
              <span>{{ column.name }}</span>
              <el-tag v-if="column.type" size="small" type="info" class="column-type">
                {{ column.type }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination" v-if="result.rows.length > pageSize">
        <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="result.rows.length"
        layout="prev, pager, next, jumper, ->, total"
        @current-change="handlePageChange"
      />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!result" class="empty-state">
      <el-empty description="暂无查询结果" :image-size="100" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import type { QueryResult } from '../../types'

interface Props {
  result?: QueryResult
}

const props = defineProps<Props>()

const currentPage = ref(1)
const pageSize = ref(100)

// 状态类型
const statusType = computed(() => {
  const map: Record<string, any> = {
    running: 'warning',
    success: 'success',
    failed: 'danger',
    idle: 'info'
  }
  return map[props.result?.status || 'idle']
})

// 状态文本
const statusText = computed(() => {
  const map: Record<string, string> = {
    running: '执行中',
    success: '执行成功',
    failed: '执行失败',
    idle: '等待执行'
  }
  return map[props.result?.status || 'idle']
})

// 分页数据
const paginatedRows = computed(() => {
  if (!props.result?.rows) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return props.result.rows.slice(start, end)
})

// 格式化时间
const formatTime = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  return `${(ms / 60000).toFixed(2)}min`
}

// 分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
}

// 导出 CSV
const exportCsv = () => {
  if (!props.result?.rows || !props.result?.columns) return

  const headers = props.result.columns.map(c => c.name).join(',')
  const rows = props.result.rows.map(row => {
    return props.result!.columns.map(col => {
      const value = row[col.name]
      if (value === null || value === undefined) return ''
      if (typeof value === 'string' && value.includes(',')) {
        return `"${value.replace(/"/g, '""')}"`
      }
      return String(value)
    }).join(',')
  })
  
  const csv = [headers, ...rows].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  saveAs(blob, `query-result-${Date.now()}.csv`)
  ElMessage.success('CSV 导出成功')
}

// 导出 Excel
const exportExcel = () => {
  if (!props.result?.rows || !props.result?.columns) return

  const data = props.result.rows.map(row => {
    const obj: Record<string, any> = {}
    props.result!.columns.forEach(col => {
      obj[col.name] = row[col.name]
    })
    return obj
  })

  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Result')
  
  const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([excelBuffer], { type: 'application/octet-stream' })
  saveAs(blob, `query-result-${Date.now()}.xlsx`)
  ElMessage.success('Excel 导出成功')
}
</script>

<style scoped>
.query-result {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.execution-time,
.row-count,
.affected-rows {
  font-size: 12px;
  color: #6b7280;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.error-alert {
  margin: 16px;
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  color: #6b7280;
}

.result-table-container {
  flex: 1;
  overflow: auto;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.column-type {
  font-weight: normal;
}

.pagination {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.empty-state {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
