<template>
  <div class="dashboard-container">
    <!-- Header Section -->
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
          style="width: 240px; margin-right: 16px;"
          @change="handleDateChange"
        />
        
        <div class="user-info">
          <span class="welcome-text">您好，{{ currentUser?.real_name || '系统管理员' }}</span>
          <el-badge :value="12" class="notification-badge">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <el-avatar :size="32" class="user-avatar">
            {{ (currentUser?.real_name || '管')[0] }}
          </el-avatar>
          <span class="username">{{ currentUser?.real_name || '系统管理员' }}</span>
        </div>
      </div>
    </div>

    <!-- Welcome Message -->
    <div class="welcome-section">
      <h2>您好，{{ currentUser?.real_name || '系统管理员' }}</h2>
      <p>欢迎使用天行建筑管理系统</p>
    </div>

    <!-- KPI Cards Row -->
    <el-row :gutter="20" class="kpi-row">
      <el-col :span="6" v-for="(card, index) in kpiCards" :key="index">
        <el-card shadow="hover" class="kpi-card" :class="`kpi-card--${card.type}`">
          <div class="kpi-content">
            <div class="kpi-icon-wrapper">
              <el-icon :size="32" :color="card.color">
                <component :is="card.icon" />
              </el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-value">{{ card.value }}</div>
              <div class="kpi-title">{{ card.title }}</div>
              <div class="kpi-trend" :class="card.trendUp ? 'trend-up' : 'trend-down'">
                较上月 {{ card.trendUp ? '↑' : '↓' }} {{ Math.abs(card.trend) }}%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">月度审批统计</span>
              <el-select v-model="timeFilter" size="small" style="width: 120px;">
                <el-option label="近6个月" value="6m" />
                <el-option label="近3个月" value="3m" />
                <el-option label="近1个月" value="1m" />
              </el-select>
            </div>
          </template>
          <div ref="approvalChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">预警分布</span>
            </div>
          </template>
          <div ref="alertChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Tables Row -->
    <el-row :gutter="20" class="tables-row">
      <el-col :span="12">
        <el-card shadow="hover" class="table-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">我的待办审批</span>
              <el-button type="primary" link @click="$router.push('/approval/pending')">查看全部</el-button>
            </div>
          </template>
          
          <el-table 
            :data="pendingApprovals" 
            stripe
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
          >
            <el-table-column prop="node_type" label="节点" min-width="120" show-overflow-tooltip />
            <el-table-column prop="version" label="版本" width="80" align="center" />
            <el-table-column label="当前步骤" min-width="140" show-overflow-tooltip>
              <template #default="{ row }">
                {{ getStepInfo(row) }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="handleApproval(row)">去处理</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="table-footer">
            <span>共 {{ pendingTotal }} 条</span>
            <el-pagination
              v-model:current-page="pendingPage"
              :page-size="5"
              layout="prev, pager, next"
              small
            />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="table-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">最新预警</span>
              <el-button type="danger" link @click="$router.push('/alerts')">查看全部</el-button>
            </div>
          </template>
          
          <el-table 
            :data="recentAlerts" 
            stripe
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: 'bold' }"
          >
            <el-table-column label="类型" width="100" align="center">
              <template #default="{ row }">
                <div class="alert-type-cell">
                  <span class="alert-dot" :style="{ backgroundColor: getAlertColor(row.alert_type) }"></span>
                  <span>{{ row.alert_type }}</span>
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
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          
          <div class="table-footer">
            <span>共 {{ alertTotal }} 条</span>
            <el-pagination
              v-model:current-page="alertPage"
              :page-size="5"
              layout="prev, pager, next"
              small
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Footer -->
    <div class="dashboard-footer">
      <span>Copyright © 2024 天行建筑 All rights reserved.</span>
      <span>版本 v2.1.0</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { Bell } from '@element-plus/icons-vue'
import { approvalApi, alertApi } from '@/api'
import { useUserStore } from '@/stores'

const router = useRouter()
const userStore = useUserStore()

// Current user
const currentUser = ref<any>(userStore.userInfo || null)

// Date range
const dateRange = ref<[string, string]>(['2024-01-01', '2024-06-30'])

// Time filter for chart
const timeFilter = ref('6m')

// KPI Data
const kpiCards = ref([
  { title: '进行中审批', value: 0, icon: 'Tickets', color: '#409EFF', trend: 12, trendUp: true, type: 'blue' },
  { title: '今日待办', value: 0, icon: 'Bell', color: '#E6A23C', trend: 8, trendUp: true, type: 'orange' },
  { title: '未解决预警', value: 0, icon: 'Warning', color: '#F56C6C', trend: 15, trendUp: false, type: 'red' },
  { title: '本月项目', value: 0, icon: 'Files', color: '#67C23A', trend: 5, trendUp: true, type: 'green' },
])

// Charts refs
const approvalChartRef = ref<HTMLDivElement>()
const alertChartRef = ref<HTMLDivElement>()
let approvalChart: echarts.ECharts | null = null
let alertChart: echarts.ECharts | null = null

// Table data
const pendingApprovals = ref<any[]>([])
const pendingTotal = ref(12)
const pendingPage = ref(1)

const recentAlerts = ref<any[]>([])
const alertTotal = ref(7)
const alertPage = ref(1)

// Mock data for pending approvals
const mockPendingApprovals = [
  { id: 1, node_type: '施工方案审批', version: 'V1.2', step: '项目经理审批', created_at: '2024-06-12 10:30' },
  { id: 2, node_type: '材料采购申请', version: 'V1.0', step: '部门负责人审批', created_at: '2024-06-12 09:15' },
  { id: 3, node_type: '设计变更申请', version: 'V2.1', step: '总工审批', created_at: '2024-06-11 16:45' },
  { id: 4, node_type: '付款申请', version: 'V1.3', step: '财务审核', created_at: '2024-06-11 14:20' },
  { id: 5, node_type: '合同变更申请', version: 'V1.1', step: '法务审核', created_at: '2024-06-10 11:05' },
]

// Mock data for alerts
const mockAlerts = [
  { id: 1, alert_type: '资料缺失', message: '项目A-施工许可证缺失', severity: 'critical', created_at: '2024-06-12 10:30' },
  { id: 2, alert_type: '超时预警', message: '项目B-设计方案审批超时', severity: 'warning', created_at: '2024-06-12 09:15' },
  { id: 3, alert_type: '超期预警', message: '项目C-材料进场超期', severity: 'medium', created_at: '2024-06-11 16:45' },
  { id: 4, alert_type: '回款提醒', message: '项目D-第3期款项未回款', severity: 'info', created_at: '2024-06-11 14:20' },
  { id: 5, alert_type: '超时预警', message: '项目E-竣工验收超时', severity: 'warning', created_at: '2024-06-10 11:05' },
]

// Methods
function getStepInfo(instance: any): string {
  if (instance.step) return instance.step
  const steps = instance.steps || []
  const current = steps.find((s: any) => s.step_status === 'pending')
  if (current) return `第${current.step_order}步`
  return '-'
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
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
    medium: '#E6A23C',
    info: '#409EFF',
  }
  return map[severity] || '#909399'
}

function getAlertColor(type: string): string {
  const map: Record<string, string> = {
    '超时预警': '#409EFF',
    '超期预警': '#67C23A',
    '回款提醒': '#E6A23C',
    '资料缺失': '#F56C6C',
  }
  return map[type] || '#909399'
}

function handleApproval(row: any) {
  router.push(`/approval/${row.id}`)
}

function handleDateChange() {
  console.log('Date range changed:', dateRange.value)
  // Reload dashboard data with new date range
  loadDashboardData()
}

// Load dashboard data
async function loadDashboardData() {
  try {
    // Use mock data for demo
    pendingApprovals.value = mockPendingApprovals
    recentAlerts.value = mockAlerts
    
    // Update KPI values
    kpiCards.value[0].value = 128
    kpiCards.value[1].value = 16
    kpiCards.value[2].value = 7
    kpiCards.value[3].value = 24
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

// Initialize charts
function initCharts() {
  // Approval trend chart
  if (approvalChartRef.value) {
    approvalChart = echarts.init(approvalChartRef.value)
    approvalChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['已批准', '已拒绝', '待处理'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['1月', '2月', '3月', '4月', '5月', '6月'],
      },
      yAxis: { type: 'value' },
      series: [
        { name: '已批准', type: 'line', data: [12, 15, 8, 20, 18, 25], smooth: true, itemStyle: { color: '#409EFF' } },
        { name: '已拒绝', type: 'line', data: [2, 1, 3, 1, 2, 0], smooth: true, itemStyle: { color: '#67C23A' } },
        { name: '待处理', type: 'bar', data: [5, 3, 8, 4, 6, 3], itemStyle: { color: '#E6A23C' } },
      ],
    })
  }
  
  // Alert distribution chart - doughnut with center number
  if (alertChartRef.value) {
    alertChart = echarts.init(alertChartRef.value)
    alertChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left', top: 'middle' },
      series: [
        {
          name: '预警类型',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: false,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          labelLine: {
            show: false,
          },
          data: [
            { value: 3, name: '超时预警', itemStyle: { color: '#409EFF' } },
            { value: 2, name: '超期预警', itemStyle: { color: '#67C23A' } },
            { value: 1, name: '回款提醒', itemStyle: { color: '#E6A23C' } },
            { value: 1, name: '资料缺失', itemStyle: { color: '#F56C6C' } },
          ],
        },
      ],
      graphic: [{
        type: 'text',
        left: 'center',
        top: '45%',
        style: {
          text: '7',
          fontSize: 32,
          fontWeight: 'bold',
          fill: '#303133',
          textAlign: 'center',
        },
      }, {
        type: 'text',
        left: 'center',
        top: '55%',
        style: {
          text: '预警总数',
          fontSize: 14,
          fill: '#909399',
          textAlign: 'center',
        },
      }],
    })
  }
}

// Handle window resize
function handleResize() {
  approvalChart?.resize()
  alertChart?.resize()
}

onMounted(() => {
  loadDashboardData()
  initCharts()
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
  padding: 20px;
  min-height: 100%;
  background: #f0f2f5;
}

/* Header Section */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.welcome-text {
  font-size: 14px;
  color: #606266;
}

.notification-badge {
  cursor: pointer;
  color: #606266;
}

.user-avatar {
  background: #409EFF;
  color: #fff;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

/* Welcome Section */
.welcome-section {
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.welcome-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.welcome-section p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

/* KPI Cards */
.kpi-row {
  margin-bottom: 20px;
}

.kpi-card {
  border-radius: 8px;
  transition: transform 0.3s;
}

.kpi-card:hover {
  transform: translateY(-4px);
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.kpi-info {
  flex: 1;
}

.kpi-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.kpi-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.kpi-trend {
  font-size: 12px;
  margin-top: 4px;
}

.trend-up {
  color: #67C23A;
}

.trend-down {
  color: #F56C6C;
}

/* Charts */
.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-container {
  height: 300px;
}

/* Tables */
.tables-row {
  margin-bottom: 20px;
}

.table-card {
  border-radius: 8px;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

/* Alert Type Cell */
.alert-type-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}

.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.severity-text {
  font-weight: 500;
}

/* Footer */
.dashboard-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  color: #909399;
  font-size: 12px;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
}
</style>
