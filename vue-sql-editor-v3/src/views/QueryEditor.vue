<template>
  <div class="query-editor-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-select
          v-model="selectedDatasourceId"
          placeholder="选择数据源"
          size="small"
          style="width: 180px"
        >
          <el-option
            v-for="ds in datasourceOptions"
            :key="ds.value"
            :label="ds.label"
            :value="ds.value"
          />
        </el-select>
        <el-select
          v-if="selectedDatasourceId"
          v-model="selectedDatabase"
          placeholder="选择数据库"
          size="small"
          style="width: 150px; margin-left: 8px"
        >
          <el-option
            v-for="db in databaseNames"
            :key="db"
            :label="db"
            :value="db"
          />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button size="small" @click="formatSql">
          <el-icon><DocumentCopy /></el-icon>
          格式化
        </el-button>
        <el-button size="small" @click="executeQuery" :loading="executing">
          <el-icon><VideoPlay /></el-icon>
          执行
        </el-button>
        <el-dropdown @command="handleExecuteCommand">
          <el-button size="small">
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="selected">执行选中的 SQL</el-dropdown-item>
              <el-dropdown-item command="current">执行当前语句</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="main-content">
      <!-- 左侧数据库浏览器 -->
      <div class="sidebar">
        <DatabaseBrowser
          :datasource-id="selectedDatasourceId"
          @insert-sql="handleInsertSql"
          @datasource-change="handleDatasourceChange"
        />
      </div>

      <!-- 右侧编辑器和结果区域 -->
      <div class="editor-area">
        <!-- 标签栏 -->
        <TabBar />

        <!-- 编辑器区域 -->
        <div class="editor-container" v-if="activeTab">
          <SqlEditor
            ref="editorRef"
            v-model="activeTab.sql"
            :dialect="currentDialect"
            @cursor-change="handleCursorChange"
            @change="handleSqlChange"
          />
        </div>

        <!-- 结果区域 -->
        <div class="result-container" v-if="activeTab">
          <QueryResult :result="activeTab.result" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentCopy, VideoPlay, ArrowDown } from '@element-plus/icons-vue'
import SqlEditor from '../components/editor/SqlEditor.vue'
import QueryResult from '../components/result/QueryResult.vue'
import DatabaseBrowser from '../components/sidebar/DatabaseBrowser.vue'
import TabBar from '../components/tabs/TabBar.vue'
import { useDatasourceStore } from '../stores/datasource'
import { useTabsStore } from '../stores/tabs'
import { useEditorStore } from '../stores/editor'
import { useMetadataStore } from '../stores/metadata'
import { executeQuery as executeQueryApi } from '../api/query'
import type { QueryResult as QueryResultType } from '../types'

const datasourceStore = useDatasourceStore()
const tabsStore = useTabsStore()
const editorStore = useEditorStore()
const metadataStore = useMetadataStore()

const editorRef = ref()
const executing = ref(false)
const selectedDatasourceId = ref<string>('')
const selectedDatabase = ref<string>('')

// 计算属性
const datasourceOptions = computed(() => datasourceStore.datasourceOptions)
const databaseNames = computed(() => metadataStore.databaseNames)
const activeTab = computed(() => tabsStore.activeTab)
const currentDialect = computed(() => editorStore.currentDialect)

// 执行查询
const executeQuery = async () => {
  if (!activeTab.value) return
  
  const sql = activeTab.value.sql.trim()
  if (!sql) {
    ElMessage.warning('请输入 SQL 语句')
    return
  }
  
  if (!selectedDatasourceId.value) {
    ElMessage.warning('请选择数据源')
    return
  }
  
  if (!selectedDatabase.value) {
    ElMessage.warning('请选择数据库')
    return
  }

  executing.value = true
  
  // 设置运行状态
  const runningResult: QueryResultType = {
    id: `query-${Date.now()}`,
    sql,
    datasourceId: selectedDatasourceId.value,
    database: selectedDatabase.value,
    status: 'running',
    startTime: Date.now()
  }
  tabsStore.updateTabResult(activeTab.value.id, runningResult)

  try {
    const result = await executeQueryApi({
      datasourceId: selectedDatasourceId.value,
      database: selectedDatabase.value,
      sql,
      maxRows: 10000
    })
    tabsStore.updateTabResult(activeTab.value.id, result)
    ElMessage.success('查询执行成功')
  } catch (error) {
    const failedResult: QueryResultType = {
      ...runningResult,
      status: 'failed',
      endTime: Date.now(),
      executionTime: Date.now() - (runningResult.startTime || Date.now()),
      error: (error as Error).message
    }
    tabsStore.updateTabResult(activeTab.value.id, failedResult)
    ElMessage.error(`查询执行失败: ${(error as Error).message}`)
  } finally {
    executing.value = false
  }
}

// 执行选中的 SQL
const executeSelectedSql = async () => {
  if (!editorRef.value || !activeTab.value) return
  
  const selectedSql = editorRef.value.getSelectedText()
  if (!selectedSql.trim()) {
    ElMessage.warning('请选中要执行的 SQL 语句')
    return
  }

  // 临时更新 SQL 并执行
  const originalSql = activeTab.value.sql
  tabsStore.updateTabSql(activeTab.value.id, selectedSql)
  await executeQuery()
  tabsStore.updateTabSql(activeTab.value.id, originalSql)
}

// 执行当前语句
const executeCurrentSql = async () => {
  if (!editorRef.value || !activeTab.value) return
  
  const currentSql = editorRef.value.getCurrentSqlStatement()
  if (!currentSql.trim()) {
    ElMessage.warning('无法找到当前 SQL 语句')
    return
  }

  // 临时更新 SQL 并执行
  const originalSql = activeTab.value.sql
  tabsStore.updateTabSql(activeTab.value.id, currentSql)
  await executeQuery()
  tabsStore.updateTabSql(activeTab.value.id, originalSql)
}

// 执行命令
const handleExecuteCommand = (command: string) => {
  switch (command) {
    case 'selected':
      executeSelectedSql()
      break
    case 'current':
      executeCurrentSql()
      break
  }
}

// 格式化 SQL
const formatSql = () => {
  if (editorRef.value) {
    editorRef.value.formatSql()
  }
}

// SQL 变化处理
const handleSqlChange = (sql: string) => {
  if (activeTab.value) {
    tabsStore.updateTabSql(activeTab.value.id, sql)
  }
}

// 光标位置变化
const handleCursorChange = (position: { line: number; column: number }) => {
  if (activeTab.value) {
    tabsStore.updateTab(activeTab.value.id, { cursorPosition: position })
  }
}

// 插入 SQL
const handleInsertSql = (sql: string) => {
  if (activeTab.value) {
    const newSql = activeTab.value.sql 
      ? activeTab.value.sql + '\n\n' + sql 
      : sql
    tabsStore.updateTabSql(activeTab.value.id, newSql)
  }
}

// 数据源变化
const handleDatasourceChange = (datasourceId: string) => {
  selectedDatasourceId.value = datasourceId
}

// 监听数据源变化
watch(selectedDatasourceId, (newVal) => {
  if (newVal) {
    metadataStore.fetchDatabases(newVal)
  }
})

// 监听数据库变化
watch(selectedDatabase, (newVal) => {
  if (newVal && selectedDatasourceId.value) {
    metadataStore.fetchTables(newVal)
    if (activeTab.value) {
      tabsStore.updateTab(activeTab.value.id, {
        datasourceId: selectedDatasourceId.value,
        database: newVal
      })
    }
  }
})

onMounted(() => {
  datasourceStore.fetchDatasources()
  tabsStore.init()
})
</script>

<style scoped>
.query-editor-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 300px;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
}

.editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-container {
  flex: 1;
  min-height: 200px;
  border-bottom: 1px solid #e5e7eb;
}

.result-container {
  height: 40%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}
</style>
