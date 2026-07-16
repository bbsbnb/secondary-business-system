import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/IndexView.vue'),
        meta: { title: '总经理驾驶舱', icon: 'Odometer' },
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/projects/ProjectList.vue'),
        meta: { title: '项目管理', icon: 'Files' },
      },
      {
        path: 'projects/:id/baseline',
        name: 'Baseline',
        component: () => import('@/views/monthly/M1Baseline.vue'),
        meta: { title: 'M1基线录入', icon: 'Document' },
      },
      {
        path: 'approval/pending',
        name: 'PendingApproval',
        component: () => import('@/views/approval/PendingView.vue'),
        meta: { title: '我的待办', icon: 'Bell' },
      },
      {
        path: 'approval/history',
        name: 'ApprovalHistory',
        component: () => import('@/views/approval/HistoryView.vue'),
        meta: { title: '我的已办', icon: 'Timer' },
      },
      {
        path: 'approval/:nodeType/create',
        name: 'CreateApproval',
        component: () => import('@/views/approval/CreateView.vue'),
        meta: { title: '发起审批', icon: 'Plus' },
      },
      {
        path: 'monthly/:nodeType',
        name: 'MonthlyNode',
        component: () => import('@/views/monthly/MonthlyForm.vue'),
        meta: { title: '月度节点' },
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/DocumentsView.vue'),
        meta: { title: '项目资料库', icon: 'FolderOpened' },
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/AlertsView.vue'),
        meta: { title: '预警中心', icon: 'Warning' },
      },
      {
        path: 'dashboards/cost',
        name: 'CostDashboard',
        component: () => import('@/views/dashboard/CostDashboard.vue'),
        meta: { title: '成本看板', icon: 'TrendCharts' },
      },
      {
        path: 'dashboards/schedule',
        name: 'ScheduleDashboard',
        component: () => import('@/views/dashboard/ScheduleDashboard.vue'),
        meta: { title: '进度看板', icon: 'Calendar' },
      },
      {
        path: 'contracts',
        name: 'Contracts',
        component: () => import('@/views/ContractView.vue'),
        meta: { title: '建造合同(M24)', icon: 'DocumentChecked' },
      },
      {
        path: 'templates',
        name: 'Templates',
        component: () => import('@/views/TemplatesView.vue'),
        meta: { title: '模板管理', icon: 'Notebook' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.public) {
    if (token) {
      next('/dashboard')
    } else {
      next()
    }
  } else {
    if (!token) {
      next('/login')
    } else {
      next()
    }
  }
  
  // Set page title
  document.title = to.meta.title ? `${to.meta.title} - 天行建筑` : '天行建筑智能管理平台'
})

export default router
