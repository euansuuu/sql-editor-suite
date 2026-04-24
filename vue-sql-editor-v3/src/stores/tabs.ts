import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TabState } from '../types'

// 生成唯一 ID
const generateId = () => `tab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

export const useTabsStore = defineStore('tabs', () => {
  // 状态
  const tabs = ref<TabState[]>([])
  const activeTabId = ref<string>('')

  // 计算属性
  const activeTab = computed(() => {
    return tabs.value.find(tab => tab.id === activeTabId.value) || null
  })

  const tabCount = computed(() => tabs.value.length)

  // 创建新标签页
  const createTab = (options?: Partial<TabState>): TabState => {
    const newTab: TabState = {
      id: generateId(),
      title: options?.title || `查询 ${tabCount.value + 1}`,
      sql: options?.sql || '',
      cursorPosition: options?.cursorPosition || { line: 0, column: 0 },
      datasourceId: options?.datasourceId,
      database: options?.database,
      result: undefined,
      history: [],
      isModified: false
    }
    tabs.value.push(newTab)
    activeTabId.value = newTab.id
    return newTab
  }

  // 关闭标签页
  const closeTab = (tabId: string) => {
    const index = tabs.value.findIndex(tab => tab.id === tabId)
    if (index === -1) return

    tabs.value.splice(index, 1)

    // 如果关闭的是当前标签页，切换到其他标签
    if (tabId === activeTabId.value && tabs.value.length > 0) {
      activeTabId.value = tabs.value[Math.max(0, index - 1)]?.id || ''
    } else if (tabs.value.length === 0) {
      activeTabId.value = ''
    }
  }

  // 切换标签页
  const switchTab = (tabId: string) => {
    if (tabs.value.some(tab => tab.id === tabId)) {
      activeTabId.value = tabId
    }
  }

  // 更新标签页内容
  const updateTab = (tabId: string, updates: Partial<TabState>) => {
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      Object.assign(tab, updates)
    }
  }

  // 更新标签页 SQL
  const updateTabSql = (tabId: string, sql: string) => {
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      tab.sql = sql
      tab.isModified = true
    }
  }

  // 更新标签页查询结果
  const updateTabResult = (tabId: string, result: TabState['result']) => {
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      tab.result = result
      if (result) {
        tab.history.unshift(result)
        // 只保留最近 50 条历史
        if (tab.history.length > 50) {
          tab.history = tab.history.slice(0, 50)
        }
      }
    }
  }

  // 清除标签页查询结果
  const clearTabResult = (tabId: string) => {
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      tab.result = undefined
    }
  }

  // 重命名标签页
  const renameTab = (tabId: string, title: string) => {
    const tab = tabs.value.find(t => t.id === tabId)
    if (tab) {
      tab.title = title
    }
  }

  // 关闭其他标签页
  const closeOtherTabs = (tabId: string) => {
    tabs.value = tabs.value.filter(tab => tab.id === tabId)
    activeTabId.value = tabId
  }

  // 关闭所有标签页
  const closeAllTabs = () => {
    tabs.value = []
    activeTabId.value = ''
  }

  // 初始化 - 默认创建一个标签页
  const init = () => {
    if (tabs.value.length === 0) {
      createTab()
    }
  }

  return {
    tabs,
    activeTabId,
    activeTab,
    tabCount,
    createTab,
    closeTab,
    switchTab,
    updateTab,
    updateTabSql,
    updateTabResult,
    clearTabResult,
    renameTab,
    closeOtherTabs,
    closeAllTabs,
    init
  }
})
