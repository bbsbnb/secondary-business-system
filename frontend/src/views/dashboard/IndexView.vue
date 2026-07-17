<template>
  <div class="dashboard-container" v-loading="loading">
    <div class="dashboard-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>驾驶舱</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="~"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          @change="handleDateChange"
        />
        <div class="user-info">
          <span class="welcome-text">您好，{{ displayName }}</span>
          <el-badge :value="pendingTotal" :hidden="pendingTotal === 0" class="notification-badge" @click="router.push('/approval/pending')">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <el-avatar :size="32" class="user-avatar">{{ displayName[0] }}</el-avatar>
          <span class="username">{{ displayName }}</span>
        </div>
      </div>
    </div>

    <div class="welcome-section">
      <h2>您好，{{ displayName }}</h2>
      <p>欢迎使用天行建筑管理系统</p>
    </div>

    <el-row :gutter="20" class="kpi-row">
      <el-col v-for="card in kpiCards" :key="card.title" :xs="24" :sm="12" :lg="6">
        <el-card shadow="hover" class="kpi-card" @click="goTo(card.path)">
          <div class="kpi-content">
            <div class="kpi-icon-wrapper">
              <el-icon :size="30" :color="card.color">
                <component :is="card.icon" />
              </el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-value">{{ card.value }}</div>
              <div class="kpi-title">{{ card.title }}</div>
              <div class="kpi-hint">{{ card.hint }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">月度审批趋势</span>
              <el-select v-model="timeFilter" size="small" style="width: 120px" @change="loadTrendData">
                <el-option label="近6个月" :value="6" />
                <el-option label="近3个月" :value="3" />
                <el-option label="近1个月" :value="1" />
              </el-select>
            </div>
          </template>
          <div ref="approvalChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">预警分布</span>
              <el-button type="danger" link @click="router.push('/alerts')">查看全部</el-button>
            </div>
          </template>
          <div ref="alertChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="tables-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="table-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">我的待办审批</span>
              <el-button type="primary" link @click="router.push('/approval/pending')">查看全部</el-button>
            </div>
          </template>

          <el-table :data="pagedPendingApprovals" stripe style="width: 100%" empty-text="暂无待办审批">
            <el-table-column prop="node_type" label="节点" min-width="100" show-overflow-tooltip />
            <el-table-column label="版本" width="80" align="center">
              <template #default="{ row }">V{{ row.version }}</template>
            </el-table-column>
            <el-table-column label="当前步骤" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">{{ getStepInfo(row) }}</template>
            </el-table-column>
            <el-table-column label="创建时间" width="150">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="90" align="center">
              <template #default>
                <el-button type="primary" size="small" @click="router.push('/approval/pending')">处理</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span>共 {{ pendingTotal }} 条</span>
            <el-pagination v-model:current-page="pendingPage" :page-size="5" :total="pendingTotal" layout="prev, pager, next" small />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" class="table-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">最新预警</span>
              <el-button type="danger" link @click="router.push('/alerts')">查看全部</el-button>
            </div>
          </template>

          <el-table :data="pagedRecentAlerts" stripe style="width: 100%" empty-text="暂无预警">
            <el-table-column label="类型" width="110" align="center">
              <template #default="{ row }">
                <div class="alert-type-cell">
                  <span class="alert-dot" :style="{ backgroundColor: getSeverityColor(row.severity) }"></span>
                  <span>{{ getAlertTypeLabel(row.alert_type) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="内容" min-width="180" show-overflow-tooltip />
            <el-table-column label="严重程度" width="90" align="center">
              <template #default="{ row }">
                <span class="severity-text" :style="{ color: getSeverityColor(row.severity) }">
                  {{ getSeverityLabel(row.severity) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="150">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span>共 {{ alertTotal }} 条</span>
            <el-pagination v-model:current-page="alertPage" :page-size="5" :total="alertTotal" layout="prev, pager, next" small />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="dashboard-footer">
      <span>Copyright 2024 天行建筑 All rights reserved.</span>
      <span>版本 v2.1.0</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { Bell, Files, Tickets, Warning } from '@element-plus/icons-vue'
import { alertApi, approvalApi, dashboardApi } from '@/api'
import { useUserStore } from '@/stores'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const currentUser = ref<any>(userStore.userInfo || null)
const displayName = computed(() => currentUser.value?.real_name || currentUser.value?.username || '系统管理员')
const dateRange = ref<[string, string]>([
  dayjs().startOf('month').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD'),
])
const timeFilter = ref(6)

const approvalChartRef = ref<HTMLDivElement>()
const alertChartRef = ref<HTMLDivElement>()
let approvalChart: echarts.ECharts | null = null
let alertChart: echarts.ECharts | null = null

const summary = ref<any>({})
const trendData = ref<any[]>([])
const recentAlerts = ref<any[]>([])
const pendingApprovals = ref<any[]>([])
const pendingPage = ref(1)
const alertPage = ref(1)

const pendingTotal = computed(() => pendingApprovals.value.length)
const alertTotal = computed(() => recentAlerts.value.length)
const pagedPendingApprovals = computed(() => paginate(pendingApprovals.value, pendingPage.value))
const pagedRecentAlerts = computed(() => paginate(recentAlerts.value, alertPage.value))

const kpiCards = computed(() => [
  {
    title: '进行中审批',
    value: summary.value.pending_approvals || 0,
    hint: '本月审批中',
    icon: Tickets,
    color: '#409EFF',
    path: '/approval/pending',
  },
  {
    title: '今日待办',
    value: pendingTotal.value,
    hint: '需要处理的审批',
    icon: Bell,
    color: '#E6A23C',
    path: '/approval/pending',
  },
  {
    title: '未解决预警',
    value: summary.value.unresolved_alerts || 0,
    hint: `严重 ${summary.value.critical_alerts || 0} / 较高 ${summary.value.warning_alerts || 0}`,
    icon: Warning,
    color: '#F56C6C',
    path: '/alerts',
  },
  {
    title: '本月项目',
    value: summary.value.active_projects || 0,
    hint: `总项目 ${summary.value.total_projects || 0}`,
    icon: Files,
    color: '#67C23A',
    path: '/projects',
  },
])

function paginate(items: any[], page: number) {
  const start = (page - 1) * 5
  return items.slice(start, start + 5)
}

async function loadDashboardData() {
  loading.value = true
  try {
    const [dashboard, pending, alerts] = await Promise.all([
      dashboardApi.getSummary(),
      approvalApi.getMyPending().catch(() => []),
      alertApi.list({ resolved: false }).catch(() => ({ items: [] })),
    ])
    const dashboardData = dashboard as any
    const alertData = alerts as any
    summary.value = {
      ...(dashboardData.summary || {}),
      unresolved_alerts: dashboardData.alerts_summary?.unresolved || 0,
    }
    recentAlerts.value = dashboardData.recent_alerts || alertData.items || []
    pendingApprovals.value = (pending as any[]) || []
    pendingPage.value = 1
    alertPage.value = 1
    await loadTrendData()
    renderAlertChart()
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
}

async function loadTrendData() {
  try {
    const data = (await dashboardApi.getMonthlyTrend({ months: timeFilter.value })) as any
    trendData.value = data.trend || []
    renderApprovalChart()
  } catch (error) {
    console.error('Failed to load trend data:', error)
  }
}

async function renderApprovalChart() {
  await nextTick()
  if (!approvalChartRef.value) return
  approvalChart ||= echarts.init(approvalChartRef.value)
  const months = trendData.value.map((item) => item.month)
  const approvals = trendData.value.map((item) => item.approvals || 0)
  approvalChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 16, top: 32, bottom: 32 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '审批数量',
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(64, 158, 255, 0.12)' },
        itemStyle: { color: '#409EFF' },
        data: approvals,
      },
    ],
  })
}

async function renderAlertChart() {
  await nextTick()
  if (!alertChartRef.value) return
  alertChart ||= echarts.init(alertChartRef.value)
  const groups = recentAlerts.value.reduce((acc: Record<string, number>, alert) => {
    const label = getSeverityLabel(alert.severity)
    acc[label] = (acc[label] || 0) + 1
    return acc
  }, {})
  const data = Object.entries(groups).map(([name, value]) => ({ name, value }))
  alertChart.setOption({
    title: {
      text: String(alertTotal.value),
      subtext: '预警总数',
      left: '58%',
      top: '43%',
      textAlign: 'center',
      itemGap: 4,
      textStyle: {
        color: '#303133',
        fontSize: 30,
        fontWeight: 'bold',
      },
      subtextStyle: {
        color: '#909399',
        fontSize: 13,
      },
    },
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left', top: 'middle' },
    series: [
      {
        name: '预警分布',
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['58%', '50%'],
        data: data.length ? data : [{ name: '暂无预警', value: 0 }],
        label: { formatter: '{b}: {c}' },
      },
    ],
  })
}

function getStepInfo(instance: any): string {
  const steps = instance.steps || []
  const current = steps.find((step: any) => step.step_status === 'pending')
  return current ? `第 ${current.step_order} 步待处理` : '-'
}

function getSeverityLabel(severity: string): string {
  const map: Record<string, string> = {
    critical: '严重',
    warning: '较高',
    medium: '中等',
    info: '一般',
  }
  return map[severity] || '未知'
}

function getSeverityColor(severity: string): string {
  const map: Record<string, string> = {
    critical: '#F56C6C',
    warning: '#E6A23C',
    medium: '#409EFF',
    info: '#67C23A',
  }
  return map[severity] || '#909399'
}

function getAlertTypeLabel(type: string): string {
  const map: Record<string, string> = {
    manual: '人工预警',
    overdue: '超时预警',
    timeout: '超时预警',
    missing: '资料缺失',
    payment: '回款提醒',
  }
  return map[type] || type || '预警'
}

function formatDate(dateStr?: string): string {
  return dateStr ? dayjs(dateStr).format('YYYY-MM-DD HH:mm') : '-'
}

function goTo(path: string) {
  router.push(path)
}

function handleDateChange() {
  loadDashboardData()
}

function handleResize() {
  approvalChart?.resize()
  alertChart?.resize()
}

onMounted(() => {
  loadDashboardData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  approvalChart?.dispose()
  alertChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100%;
  padding: 20px;
  background: #f0f2f5;
}

.dashboard-header,
.header-right,
.user-info,
.card-header,
.table-footer,
.alert-type-cell {
  display: flex;
  align-items: center;
}

.dashboard-header {
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-right,
.user-info {
  gap: 16px;
}

.user-info {
  gap: 8px;
}

.welcome-text,
.username {
  color: #303133;
  font-size: 14px;
}

.notification-badge {
  color: #606266;
  cursor: pointer;
}

.user-avatar {
  background: #409eff;
  color: #fff;
}

.welcome-section {
  margin-bottom: 20px;
  padding: 20px;
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
}

.welcome-section h2 {
  margin: 0 0 8px;
  font-size: 24px;
}

.welcome-section p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.kpi-row,
.charts-row,
.tables-row {
  margin-bottom: 20px;
}

.kpi-card,
.chart-card,
.table-card {
  border-radius: 8px;
}

.kpi-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.kpi-card:hover {
  transform: translateY(-3px);
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-icon-wrapper {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 8px;
}

.kpi-value {
  color: #303133;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.1;
}

.kpi-title {
  margin-top: 4px;
  color: #606266;
  font-size: 14px;
}

.kpi-hint {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.card-header,
.table-footer {
  justify-content: space-between;
}

.card-title {
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.chart-container {
  height: 300px;
}

.table-footer {
  margin-top: 16px;
  padding-top: 16px;
  color: #606266;
  border-top: 1px solid #ebeef5;
}

.alert-type-cell {
  justify-content: center;
  gap: 6px;
}

.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.severity-text {
  font-weight: 600;
}

.dashboard-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  padding: 16px 0;
  color: #909399;
  font-size: 12px;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 900px) {
  .dashboard-header,
  .header-right,
  .dashboard-footer {
    align-items: stretch;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
