<template>
  <div class="schedule-dashboard">
    <div class="page-header">
      <div>
        <h2>进度看板</h2>
        <p>按项目、里程碑和关键任务跟踪计划执行情况</p>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedProject" size="default" style="width: 180px">
          <el-option label="全部项目" value="all" />
          <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-date-picker
          v-model="month"
          type="month"
          format="YYYY-MM"
          value-format="YYYY-MM"
          style="width: 140px"
        />
      </div>
    </div>

    <el-row :gutter="16" class="summary-row">
      <el-col v-for="item in summaryCards" :key="item.label" :xs="12" :sm="12" :md="6">
        <el-card shadow="never" class="summary-card">
          <div class="summary-label">{{ item.label }}</div>
          <div class="summary-value" :style="{ color: item.color }">{{ item.value }}</div>
          <div class="summary-note">{{ item.note }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :lg="15">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span>月度计划完成趋势</span>
              <el-tag type="success" effect="plain">总体可控</el-tag>
            </div>
          </template>
          <div ref="trendChartRef" class="trend-chart"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card shadow="never" class="panel-card milestones-card">
          <template #header>
            <div class="card-header">
              <span>关键里程碑</span>
              <el-button link type="primary">查看全部</el-button>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="milestone in milestones"
              :key="milestone.name"
              :timestamp="milestone.date"
              :type="milestone.type"
              placement="top"
            >
              <div class="milestone-title">{{ milestone.name }}</div>
              <div class="milestone-desc">{{ milestone.owner }} · {{ milestone.status }}</div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span>项目进度明细</span>
              <el-segmented v-model="statusFilter" :options="statusOptions" />
            </div>
          </template>
          <el-table :data="filteredProjects" stripe style="width: 100%">
            <el-table-column prop="code" label="项目编号" width="120" />
            <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="manager" label="负责人" width="100" />
            <el-table-column label="完成率" min-width="180">
              <template #default="{ row }">
                <div class="progress-cell">
                  <el-progress :percentage="row.progress" :status="getProgressStatus(row)" />
                  <span>{{ row.progress }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="currentStage" label="当前阶段" min-width="140" show-overflow-tooltip />
            <el-table-column prop="plannedFinish" label="计划完成" width="120" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row)" effect="plain">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="panel-card risk-card">
          <template #header>
            <div class="card-header">
              <span>进度风险</span>
              <el-tag type="warning" effect="plain">{{ scheduleRisks.length }} 项</el-tag>
            </div>
          </template>
          <div v-for="risk in scheduleRisks" :key="risk.title" class="risk-item">
            <div class="risk-topline">
              <span>{{ risk.title }}</span>
              <el-tag :type="risk.type" size="small">{{ risk.level }}</el-tag>
            </div>
            <p>{{ risk.detail }}</p>
            <div class="risk-meta">{{ risk.project }} · {{ risk.owner }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'

type ProjectStatus = '正常' | '滞后' | '预警'

interface ScheduleProject {
  id: string
  code: string
  name: string
  manager: string
  progress: number
  plannedProgress: number
  currentStage: string
  plannedFinish: string
  status: ProjectStatus
}

const month = ref(dayjs().format('YYYY-MM'))
const selectedProject = ref('all')
const statusFilter = ref('全部')
const trendChartRef = ref<HTMLDivElement>()
let trendChart: echarts.ECharts | null = null

const statusOptions = ['全部', '正常', '预警', '滞后']

const projects = ref<ScheduleProject[]>([
  {
    id: 'p1',
    code: 'TX-001',
    name: '天行总部综合楼',
    manager: '张三',
    progress: 78,
    plannedProgress: 75,
    currentStage: '主体结构收尾',
    plannedFinish: '2026-09-20',
    status: '正常',
  },
  {
    id: 'p2',
    code: 'TX-002',
    name: '滨江商业中心二期',
    manager: '李四',
    progress: 54,
    plannedProgress: 62,
    currentStage: '机电安装',
    plannedFinish: '2026-10-12',
    status: '预警',
  },
  {
    id: 'p3',
    code: 'TX-003',
    name: '东城学校改扩建',
    manager: '王五',
    progress: 43,
    plannedProgress: 58,
    currentStage: '砌体施工',
    plannedFinish: '2026-08-30',
    status: '滞后',
  },
  {
    id: 'p4',
    code: 'TX-004',
    name: '云湖住宅精装修',
    manager: '赵六',
    progress: 86,
    plannedProgress: 82,
    currentStage: '分户验收',
    plannedFinish: '2026-07-31',
    status: '正常',
  },
])

const milestones = [
  { name: '总部综合楼主体封顶', owner: '工程部', status: '按期推进', date: '2026-07-25', type: 'success' as const },
  { name: '商业中心机电样板验收', owner: '项目部', status: '需协调材料到场', date: '2026-08-03', type: 'warning' as const },
  { name: '学校改扩建二层结构验收', owner: '工程部', status: '滞后 5 天', date: '2026-08-10', type: 'danger' as const },
  { name: '云湖住宅竣工预验收', owner: '资料室', status: '资料同步中', date: '2026-08-18', type: 'primary' as const },
]

const scheduleRisks = [
  {
    title: '材料到场影响安装节点',
    detail: '桥架与配电箱到货晚于计划，预计影响机电安装 3 天。',
    project: '滨江商业中心二期',
    owner: '采购部',
    level: '中风险',
    type: 'warning' as const,
  },
  {
    title: '砌体班组产能不足',
    detail: '现场实际投入人数低于计划，连续两周产值偏低。',
    project: '东城学校改扩建',
    owner: '工程部',
    level: '高风险',
    type: 'danger' as const,
  },
  {
    title: '验收资料补齐',
    detail: '精装修分项资料仍有缺项，需在预验收前闭合。',
    project: '云湖住宅精装修',
    owner: '资料室',
    level: '低风险',
    type: 'info' as const,
  },
]

const statusTypeMap: Record<ProjectStatus, 'success' | 'warning' | 'danger'> = {
  正常: 'success',
  预警: 'warning',
  滞后: 'danger',
}

const visibleProjects = computed(() => {
  if (selectedProject.value === 'all') return projects.value
  return projects.value.filter((project) => project.id === selectedProject.value)
})

const filteredProjects = computed(() => {
  if (statusFilter.value === '全部') return visibleProjects.value
  return visibleProjects.value.filter((project) => project.status === statusFilter.value)
})

const summaryCards = computed(() => {
  const rows = visibleProjects.value
  const averageProgress = rows.length
    ? Math.round(rows.reduce((sum, item) => sum + item.progress, 0) / rows.length)
    : 0
  const delayedCount = rows.filter((item) => item.status === '滞后').length
  const warningCount = rows.filter((item) => item.status === '预警').length
  const milestoneCount = milestones.length

  return [
    { label: '平均完成率', value: `${averageProgress}%`, note: '较计划偏差 +1.5%', color: '#409EFF' },
    { label: '在建项目', value: `${rows.length}`, note: '当前筛选范围', color: '#67C23A' },
    { label: '风险项目', value: `${warningCount + delayedCount}`, note: `${delayedCount} 个已滞后`, color: '#E6A23C' },
    { label: '本月里程碑', value: `${milestoneCount}`, note: '2 个需重点跟进', color: '#F56C6C' },
  ]
})

function getProgressStatus(row: ScheduleProject) {
  if (row.status === '滞后') return 'exception'
  if (row.status === '预警') return 'warning'
  return 'success'
}

function getStatusTagType(row: ScheduleProject) {
  return statusTypeMap[row.status]
}

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()
}

function updateTrendChart() {
  if (!trendChart) return
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['计划完成率', '实际完成率'] },
    grid: { left: 36, right: 24, top: 48, bottom: 28, containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: ['3月', '4月', '5月', '6月', '7月', '8月'] },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
    series: [
      {
        name: '计划完成率',
        type: 'line',
        smooth: true,
        data: [22, 36, 49, 63, 76, 88],
        lineStyle: { color: '#909399', type: 'dashed' },
        itemStyle: { color: '#909399' },
      },
      {
        name: '实际完成率',
        type: 'line',
        smooth: true,
        areaStyle: { color: 'rgba(64, 158, 255, 0.12)' },
        data: selectedProject.value === 'p3' ? [18, 29, 38, 43, 49, 58] : [24, 38, 51, 64, 78, 90],
        itemStyle: { color: '#409EFF' },
      },
    ],
  })
}

function handleResize() {
  trendChart?.resize()
}

watch(selectedProject, () => {
  nextTick(updateTrendChart)
})

onMounted(() => {
  initTrendChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
})
</script>

<style scoped>
.schedule-dashboard {
  padding: 20px;
  min-height: 100%;
  background: #f0f2f5;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 18px 20px;
  background: #fff;
  border-radius: 8px;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-row,
.content-row {
  margin-bottom: 16px;
}

.summary-card,
.panel-card {
  border-radius: 8px;
}

.summary-label {
  color: #909399;
  font-size: 13px;
}

.summary-value {
  margin-top: 8px;
  font-size: 30px;
  line-height: 1;
  font-weight: 700;
}

.summary-note {
  margin-top: 8px;
  color: #606266;
  font-size: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.trend-chart {
  height: 320px;
}

.milestones-card,
.risk-card {
  min-height: 402px;
}

.milestone-title {
  color: #303133;
  font-weight: 600;
  line-height: 1.4;
}

.milestone-desc {
  margin-top: 4px;
  color: #606266;
  font-size: 13px;
}

.progress-cell {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) 42px;
  align-items: center;
  gap: 10px;
}

.risk-item {
  padding: 14px 0;
  border-bottom: 1px solid #ebeef5;
}

.risk-item:first-of-type {
  padding-top: 0;
}

.risk-item:last-child {
  border-bottom: 0;
}

.risk-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #303133;
  font-weight: 600;
}

.risk-item p {
  margin: 8px 0;
  color: #606266;
  line-height: 1.5;
  font-size: 13px;
}

.risk-meta {
  color: #909399;
  font-size: 12px;
}

@media (max-width: 768px) {
  .schedule-dashboard {
    padding: 12px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .trend-chart {
    height: 260px;
  }
}
</style>
