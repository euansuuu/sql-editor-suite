<template>
  <div class="tab-bar">
    <div class="tabs-container">
      <div
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-item', { active: tab.id === activeTabId }]"
        @click="switchTab(tab.id)"
        @contextmenu.prevent="handleContextMenu($event, tab)"
      >
        <span class="tab-title">{{ tab.title }}</span>
        <span v-if="tab.isModified" class="modified-dot">●</span>
        <el-icon
          class="close-btn"
          @click.stop="closeTab(tab.id)"
        >
          <Close />
        </el-icon>
      </div>
    </div>
    <div class="tabs-actions">
      <el-button size="small" @click="createNewTab">
        <el-icon><Plus /></el-icon>
        新建
      </el-button>
      <el-dropdown @command="handleDropdownCommand">
        <el-button size="small">
          <el-icon><MoreFilled /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="close-other" :disabled="tabs.length <= 1">关闭其他</el-dropdown-item>
            <el-dropdown-item command="close-all">关闭全部</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Plus, MoreFilled, Close } from '@element-plus/icons-vue'
import { useTabsStore } from '../../stores/tabs'
import type { TabState } from '../../types'

const tabsStore = useTabsStore()

const tabs = computed(() => tabsStore.tabs)
const activeTabId = computed(() => tabsStore.activeTabId)

// 新建标签页
const createNewTab = () => {
  tabsStore.createTab()
}

// 关闭标签页
const closeTab = (tabId: string) => {
  tabsStore.closeTab(tabId)
}

// 切换标签页
const switchTab = (tabId: string) => {
  tabsStore.switchTab(tabId)
}

// 右键菜单
const handleContextMenu = (event: MouseEvent, tab: TabState) => {
  // 可以在这里实现自定义右键菜单
  console.log('Context menu for tab:', tab.id)
}

// 下拉菜单命令
const handleDropdownCommand = (command: string) => {
  switch (command) {
    case 'close-other':
      if (activeTabId.value) {
        tabsStore.closeOtherTabs(activeTabId.value)
      }
      break
    case 'close-all':
      tabsStore.closeAllTabs()
      // 关闭全部后新建一个空标签页
      if (tabsStore.tabs.length === 0) {
        tabsStore.createTab()
      }
      break
  }
}
</script>

<style scoped>
.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f5f7fa;
  border-bottom: 1px solid #e5e7eb;
  height: 40px;
  padding: 0 8px;
}

.tabs-container {
  display: flex;
  align-items: center;
  flex: 1;
  overflow-x: auto;
  gap: 2px;
  padding: 4px 0;
}

.tabs-container::-webkit-scrollbar {
  height: 4px;
}

.tabs-container::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
  transition: all 0.2s;
}

.tab-item:hover {
  background: #f3f4f6;
}

.tab-item.active {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

.tab-title {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.modified-dot {
  font-size: 10px;
  color: #f59e0b;
}

.tab-item.active .modified-dot {
  color: #fde047;
}

.close-btn {
  font-size: 14px;
  opacity: 0.6;
  padding: 2px;
  border-radius: 2px;
}

.close-btn:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

.tabs-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-left: 8px;
  border-left: 1px solid #e5e7eb;
}
</style>
