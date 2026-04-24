<template>
  <div class="query-history-page">
    <div class="page-header">
      <h2>查询历史</h2>
    </div>

    <div class="page-content">
      <el-table
        :data="historyList"
        border
        v-loading="loading"
      >
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sql" label="SQL 语句" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <code class="sql-preview">{{ row.sql.slice(0, 100) }}{{ row.sql.length > 100 ? '...' : '' }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="database" label="数据库" width="120" />
        <el-table-column prop="executionTime" label="执行时间" width="100">
          <template #default="{ row }">
            {{ row.executionTime !== undefined ? formatTime(row.executionTime) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="rows" label="行数" width="80">
          <template #default="{ row }">
            {{ row.rows?.length || (row.affectedRows !== undefined ? row.affectedRows : '-') }}
          </template>
        </el-table-column>
        <el-table-column prop="startTime" label="开始时间" width="180">
          <template #default="{ row }">
            {{ row.startTime ? new Date(row.startTime).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">
              查看
            </el-button>
            <el-button size="small" @click="copySql(row)">
              复制
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper, ->, total"
          @current-change="fetchHistory"
        />
      </div>
    </div>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="查询详情"
      width="80%"
      top="5vh"
    >
      <div v-if="currentDetail" class="detail-content">
        <el-descriptions :column="3" size="small" border>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentDetail.status)" size="small">
              {{ getStatusText(currentDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数据库">{{ currentDetail.database }}</el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{ currentDetail.executionTime !== undefined ? formatTime(currentDetail.executionTime) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ currentDetail.startTime ? new Date(currentDetail.startTime).toLocaleString('zh-CN') : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ currentDetail.endTime ? new Date(currentDetail.endTime).toLocaleString('zh-CN') : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="结果行数">
            {{ currentDetail.rows?.length || (currentDetail.affectedRows !== undefined ? currentDetail.affectedRows : '-') }}
          </el-descriptions-item>
        </el-descriptions>

        <h4>SQL 语句</h4>
        <pre class="sql-detail">{{ currentDetail.sql }}</pre>

        <template v-if="currentDetail.status === 'success' && currentDetail.rows && currentDetail.columns">
          <h4>查询结果</h4>
          <div class="result-table">
            <el-table
              :data="currentDetail.rows.slice(0, 100)"
              border
              size="small"
              max-height="300"
            >
              <el-table-column
                v-for="column in currentDetail.columns"
                :key="column.name"
                :prop="column.name"
                :label="column.name"
                min-width="100"
                show-overflow-tooltip
              />
            </el-table>
          </div>
        </template>

        <template v-if="currentDetail.status === 'failed' && currentDetail.error">
          <h4>错误信息</h4>
          <el-alert :title="currentDetail.error" type="error" :closable="false" show-icon />
        </template>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="copyCurrentDetailSql">
          复制 SQL
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { QueryResult } from '../types'
import { getQueryHistory } from '../api/query'

const loading = ref(false)
const historyList = ref<QueryResult[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const currentDetail = ref<QueryResult | null>(null)

// 获取状态类型
const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    running: 'warning',
    success: 'success',
    failed: 'danger',
    idle: 'info'
  }
  return map[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    running: '执行中',
    success: '成功',
    failed: '失败',
    idle: '等待'
  }
  return map[status] || status
}

// 格式化时间
const formatTime = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
  return `${(ms / 60000).toFixed(2)}min`
}

// 获取查询历史
const fetchHistory = async () => {
  loading.value = true
  try {
    // 这里调用 API，暂时使用模拟数据
    // const result = await getQueryHistory({ page: currentPage.value, pageSize: pageSize.value })
    // historyList.value = result.list
    // total.value = result.total
    
    // 模拟数据
    historyList.value = []
    total.value = 0
  } catch (error) {
    ElMessage.error('获取查询历史失败')
  } finally {
    loading.value = false
  }
}

// 查看详情
const viewDetail = (item: QueryResult) => {
  currentDetail.value = item
  detailVisible.value = true
}

// 复制 SQL
const copySql = (item: QueryResult) => {
  navigator.clipboard.writeText(item.sql)
  ElMessage.success('已复制到剪贴板')
}

// 复制当前详情的 SQL
const copyCurrentDetailSql = () => {
  if (currentDetail.value) {
    copySql(currentDetail.value)
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.query-history-page {
  padding: 24px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.page-content {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
}

.sql-preview {
  font-family: monospace;
  font-size: 12px;
  color: #374151;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.detail-content {
  h4 {
    margin: 20px 0 12px;
    font-size: 14px;
    font-weight: 600;
    color: #374151;
  }
}

.sql-detail {
  padding: 16px;
  background: #f3f4f6;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow: auto;
}

.result-table {
  margin-top: 12px;
}
</style>
