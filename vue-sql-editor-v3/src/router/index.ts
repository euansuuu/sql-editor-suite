import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/QueryEditor.vue'),
    meta: { title: 'SQL 查询编辑器' }
  },
  {
    path: '/datasources',
    name: 'Datasources',
    component: () => import('../views/Datasources.vue'),
    meta: { title: '数据源管理' }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/QueryHistory.vue'),
    meta: { title: '查询历史' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 页面标题
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'SQL Editor'} - Vue SQL Editor`
  next()
})

export default router
