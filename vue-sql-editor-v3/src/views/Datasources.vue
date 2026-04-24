<template>
  <div class="datasources-page">
    <div class="page-header">
      <h2>数据源管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建数据源
      </el-button>
    </div>

    <div class="page-content">
      <el-table
        :data="datasourceStore.datasources"
        v-loading="datasourceStore.loading"
        border
      >
        <el-table-column prop="name" label="名称" min-width="150" />
        <el-table-column prop="type" label="SQL 方言" width="140">
          <template #default="{ row }">
            <el-tag size="small">{{ getDialectLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="host" label="主机" min-width="150" />
        <el-table-column prop="port" label="端口" width="80" />
        <el-table-column prop="database" label="数据库" width="120" />
        <el-table-column prop="authType" label="认证方式" width="120">
          <template #default="{ row }">
            {{ row.authType === 'basic' ? '用户名密码' : 'Kerberos' }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="testConnection(row)">
              测试连接
            </el-button>
            <el-button size="small" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="confirmDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingDatasource ? '编辑数据源' : '新建数据源'"
      width="600px"
      :close-on-click-modal="false"
    >
      <DatasourceForm
        ref="formRef"
        :datasource="editingDatasource"
        @success="handleSuccess"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import DatasourceForm from '../components/datasource/DatasourceForm.vue'
import { useDatasourceStore } from '../stores/datasource'
import type { DataSource } from '../types'

const datasourceStore = useDatasourceStore()

const dialogVisible = ref(false)
const editingDatasource = ref<DataSource | null>(null)
const formRef = ref()

// 方言标签
const getDialectLabel = (type: string) => {
  const map: Record<string, string> = {
    hive: 'Hive SQL',
    impala: 'Impala SQL',
    spark: 'Spark SQL',
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    trino: 'Trino/Presto'
  }
  return map[type] || type
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 打开新建对话框
const openCreateDialog = () => {
  editingDatasource.value = null
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (datasource: DataSource) => {
  editingDatasource.value = datasource
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (formRef.value) {
    await formRef.value.submit()
  }
}

// 成功处理
const handleSuccess = () => {
  dialogVisible.value = false
  datasourceStore.fetchDatasources()
}

// 测试连接
const testConnection = async (datasource: DataSource) => {
  const result = await datasourceStore.testConnection(datasource)
  if (result.success) {
    ElMessage.success('连接测试成功！')
  } else {
    ElMessage.error(`连接测试失败: ${result.message || '未知错误'}`)
  }
}

// 确认删除
const confirmDelete = async (datasource: DataSource) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源「${datasource.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await datasourceStore.removeDatasource(datasource.id)
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  datasourceStore.fetchDatasources()
})
</script>

<style scoped>
.datasources-page {
  padding: 24px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
}
</style>
