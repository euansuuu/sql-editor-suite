<template>
  <div class="database-browser">
    <!-- 数据源选择 -->
    <div class="datasource-selector">
      <el-select
        v-model="selectedDatasourceId"
        placeholder="选择数据源"
        style="width: 100%"
        size="small"
        @change="handleDatasourceChange"
      >
        <el-option
          v-for="ds in datasourceOptions"
          :key="ds.value"
          :label="ds.label"
          :value="ds.value"
        />
      </el-select>
    </div>

    <!-- 刷新按钮 -->
    <div class="toolbar">
      <el-button size="small" @click="refreshMetadata" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 数据库树 -->
    <el-tree
      ref="treeRef"
      :data="treeData"
      :props="{ children: 'children', label: 'label' }"
      v-model:expanded-keys="expandedKeys"
      node-key="id"
      :loading="loading"
      @node-click="handleNodeClick"
      :filter-node-method="filterNode"
      class="database-tree"
    >
      <template #default="{ node, data }">
        <div class="tree-node">
          <el-icon v-if="data.type === 'database'" class="node-icon"><FolderOpened /></el-icon>
          <el-icon v-else-if="data.type === 'table'" class="node-icon"><Document /></el-icon>
          <el-icon v-else-if="data.type === 'view'" class="node-icon"><View /></el-icon>
          <span class="node-label">{{ data.label }}</span>
        </div>
      </template>
    </el-tree>

    <!-- 表详情 -->
    <div v-if="currentTable" class="table-detail">
      <div class="detail-header">
        <span class="detail-title">{{ currentTable.name }}</span>
        <el-button size="small" link @click="closeTableDetail">关闭</el-button>
      </div>
      <div class="detail-content">
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="类型">{{ currentTable.type === 'table' ? '表' : '视图' }}</el-descriptions-item>
          <el-descriptions-item label="注释" v-if="currentTable.comment">{{ currentTable.comment }}</el-descriptions-item>
          <el-descriptions-item label="行数" v-if="currentTable.rowCount !== undefined">{{ currentTable.rowCount.toLocaleString() }}</el-descriptions-item>
        </el-descriptions>
        
        <h4 class="columns-title">列信息</h4>
        <el-table :data="currentTable.columns" size="small" border style="width: 100%">
          <el-table-column prop="name" label="名称" min-width="120" />
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="comment" label="注释" min-width="150" />
        </el-table>

        <div class="table-actions">
          <el-button size="small" @click="insertSelectQuery">
            插入 SELECT *
          </el-button>
          <el-button size="small" @click="insertCountQuery">
            插入 COUNT
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { FolderOpened, Document, View, Refresh } from '@element-plus/icons-vue'
import { useDatasourceStore } from '../../stores/datasource'
import { useMetadataStore } from '../../stores/metadata'
import { useEditorStore } from '../../stores/editor'

interface Props {
  datasourceId?: string
}

interface Emits {
  (e: 'insert-sql', sql: string): void
  (e: 'datasource-change', datasourceId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const datasourceStore = useDatasourceStore()
const metadataStore = useMetadataStore()
const editorStore = useEditorStore()

const treeRef = ref()
const selectedDatasourceId = ref<string>('')

// 数据源选项
const datasourceOptions = computed(() => datasourceStore.datasourceOptions)
const loading = computed(() => metadataStore.loading)
const expandedKeys = computed({
  get: () => metadataStore.expandedKeys,
  set: (val) => { metadataStore.expandedKeys = val }
})
const currentTable = computed(() => metadataStore.currentTable)

// 树数据
const treeData = computed(() => {
  return metadataStore.databases.map(db => ({
    id: db.name,
    label: db.name,
    type: 'database',
    isLeaf: false,
    children: db.tables.map(table => ({
      id: `${db.name}.${table.name}`,
      label: table.name,
      type: table.type,
      isLeaf: true
    }))
  }))
})

// 处理数据源变化
const handleDatasourceChange = (datasourceId: string) => {
  metadataStore.fetchDatabases(datasourceId)
  emit('datasource-change', datasourceId)
}

// 节点点击
const handleNodeClick = async (data: any, node: any) => {
  if (data.type === 'database') {
    // 点击数据库，加载表列表
    if (!node.expanded) {
      await metadataStore.fetchTables(data.label)
    }
  } else if (data.type === 'table' || data.type === 'view') {
    // 点击表，加载表详情
    const [database, table] = data.id.split('.')
    await metadataStore.fetchTableDetail(table, database)
  }
}

// 刷新元数据
const refreshMetadata = async () => {
  if (!selectedDatasourceId.value) {
    ElMessage.warning('请先选择数据源')
    return
  }
  await metadataStore.fetchDatabases(selectedDatasourceId.value)
  ElMessage.success('元数据刷新成功')
}

// 关闭表详情
const closeTableDetail = () => {
  metadataStore.currentTable = null
}

// 插入 SELECT * 查询
const insertSelectQuery = () => {
  if (!currentTable.value) return
  
  const db = metadataStore.currentDatabase
  const table = currentTable.value.name
  const sql = editorStore.generateSelectQuery(db, table)
  emit('insert-sql', sql)
  ElMessage.success('已插入 SELECT 查询')
}

// 插入 COUNT 查询
const insertCountQuery = () => {
  if (!currentTable.value) return
  
  const db = metadataStore.currentDatabase
  const table = currentTable.value.name
  const sql = editorStore.generateCountQuery(db, table)
  emit('insert-sql', sql)
  ElMessage.success('已插入 COUNT 查询')
}

// 树节点过滤
const filterNode = (value: string, data: any) => {
  if (!value) return true
  return data.label.includes(value)
}

// 初始化数据源
watch(() => props.datasourceId, (newVal) => {
  if (newVal && newVal !== selectedDatasourceId.value) {
    selectedDatasourceId.value = newVal
    handleDatasourceChange(newVal)
  }
}, { immediate: true })

// 初始化
datasourceStore.fetchDatasources()
</script>

<style scoped>
.database-browser {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #e5e7eb;
}

.datasource-selector {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar {
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.database-tree {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
}

.node-icon {
  font-size: 14px;
  color: #6b7280;
}

.node-label {
  flex: 1;
  font-size: 13px;
}

.table-detail {
  border-top: 1px solid #e5e7eb;
  max-height: 50%;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #e5e7eb;
}

.detail-title {
  font-weight: 600;
  font-size: 14px;
}

.detail-content {
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.columns-title {
  margin: 16px 0 8px;
  font-size: 13px;
  font-weight: 600;
}

.table-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
</style>
