<template>
  <el-config-provider :locale="zhCn">
    <div id="app">
      <!-- 顶部导航 -->
      <el-menu
        :default-active="activeMenu"
        mode="horizontal"
        router
        class="nav-menu"
      >
        <el-menu-item index="/">
          <el-icon><DataLine /></el-icon>
          <span>查询编辑器</span>
        </el-menu-item>
        <el-menu-item index="/datasources">
          <el-icon><Connection /></el-icon>
          <span>数据源管理</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>查询历史</span>
        </el-menu-item>
      </el-menu>

      <!-- 主内容 -->
      <router-view />
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { DataLine, Connection, Clock } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #1f2937;
  background: #fff;
}

#app {
  display: flex;
  flex-direction: column;
}

.nav-menu {
  border-bottom: 1px solid #e5e7eb;
}

.nav-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
}
</style>
