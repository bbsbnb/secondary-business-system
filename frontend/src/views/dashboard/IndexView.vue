<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- KPI Cards -->
      <el-col :span="6" v-for="card in kpiCards" :key="card.title">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-content">
            <div class="kpi-icon" :style="{ background: card.color }">
              <el-icon :size="32"><component :is="card.icon" /></el-icon>
            </div>
            <div class="kpi-info">
              <div class="kpi-value">{{ card.value }}</div>
              <div class="kpi-title">{{ card.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts Row -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>月度审批统计</span>
            </div>
          </template>
          <div ref="approvalChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>预警分布</span>
            </div>
          </template>
          <div ref="alertChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activity & Pending Approvals -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>我的待办审批</span>
              <el-button type="primary" link @click="$router.push('/approval/pending')">查看全部</el-button>
            </div>
          </template>
          
          <el-table :data="pendingApprovals" style="width: 100%">
            <el-table-column prop="node_type" label="节点" width="80" />
            <el-table-column prop="version" label="版本" width="70" />
            <el-table-column label="当前步骤" min-width="150">
              <template #default="{ row }">
                {{ getStepInfo(row) }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="$router.push(`/approval/${row.id}`)">处理</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!pendingApprovals.length" description="暂无待办" :image-size="80" />
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新预警</span>
              <el-button type="danger" link @click="$router.push('/alerts')">查看全部</el-button>
            </div>
          </template>
          
          <el-table :data="recentAlerts" style="width: 100%">
            <el-table-column label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">{{ row.alert_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column label="严重程度" width="80">
              <template #default="{ row }">
                <el-icon :size="16" :color="getSeverityColor(row.severity)">
                  <WarningFilled v-if="row.severity === 'critical'" />
                  <Warning v-else-if="row.severity === 'warning'" />
                  <InfoFilled v-else />
                </el-icon>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">
                {{ formatTimeAgo(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!recentAlerts.length" description="暂无预警" :image-size="80" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { approvalApi, alertApi } from '@/api'

// KPI Data
const kpiCards = ref([
  { title: '进行中审批', value: 0, icon: 'Tickets', color: '#409EFF' },
  { title: '今日待办', value: 0, icon: 'Bell', color: '#E6A23C' },
  { title: '未解决预警', value: 0, icon: 'Warning', color: '#F56C6C' },
  { title: '本月项目', value: 0, icon: 'Files', color: '#67C23A' },
])

// Charts
const approvalChartRef = ref<HTMLDivElement>()
const alertChartRef = ref<HTMLDivElement>()

// Data
const pendingApprovals = ref<any[]>([])
const recentAlerts = ref<any[]>([])

// Methods
function getStepInfo(instance: any): string {
  const steps = instance.steps || []
  const current = steps.find((s: any) => s.step_status === 'pending')
  if (current) return `第${current.step_order}步`
  return '-'
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

function formatTimeAgo(dateStr: string): string {
  return dayjs(dateStr).fromNow()
}

function getSeverityType(severity: string): string {
  const map: Record<string, string> = {
    critical: 'danger',
    warning: 'warning',
    info: 'info',
  }
  return map[severity] || 'info'
}

function getSeverityColor(severity: string): string {
  const map: Record<string, string> = {
    critical: '#F56C6C',
    warning: '#E6A23C',
    info: '#909399',
  }
  return map[severity] || '#909399'
}

// Load data
async function loadDashboardData() {
  try {
    // Load pending approvals
    const pending = await approvalApi.myPending()
    pendingApprovals.value = pending || []
    kpiCards.value[0].value = pending?.length || 0
    
    // Load alerts
    const alerts = await alertApi.unresolved()
    recentAlerts.value = (alerts || []).slice(0, 5)
    kpiCards.value[2].value = alerts?.length || 0
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

// Initialize charts
function initCharts() {
  // Approval trend chart
  if (approvalChartRef.value) {
    const chart = echarts.init(approvalChartRef.value)
    chart.setOption({
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
        { name: '已批准', type: 'line', data: [12, 15, 8, 20, 18, 25], smooth: true },
        { name: '已拒绝', type: 'line', data: [2, 1, 3, 1, 2, 0], smooth: true },
        { name: '待处理', type: 'bar', data: [5, 3, 8, 4, 6, 3] },
      ],
    })
  }
  
  // Alert distribution chart
  if (alertChartRef.value) {
    const chart = echarts.init(alertChartRef.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [
        {
          name: '预警类型',
          type: 'pie',
          radius: '50%',
          data: [
            { value: 3, name: '超时预警' },
            { value: 2, name: '超概预警' },
            { value: 1, name: '回款提醒' },
            { value: 1, name: '资料缺失' },
          ],
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
        },
      ],
    })
  }
}

onMounted(() => {
  loadDashboardData()
  initCharts()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.kpi-card {
  margin-bottom: 20px;
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.kpi-info {
  flex: 1;
}

.kpi-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.kpi-title {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
