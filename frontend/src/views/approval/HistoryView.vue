<template>
  <div class="history-view">
    <div class="summary-grid">
      <el-card shadow="never">
        <div class="summary-label">已办总数</div>
        <div class="summary-value">{{ histories.length }}</div>
      </el-card>
      <el-card shadow="never">
        <div class="summary-label">已通过</div>
        <div class="summary-value success">{{ approvedCount }}</div>
      </el-card>
      <el-card shadow="never">
        <div class="summary-label">已驳回</div>
        <div class="summary-value danger">{{ rejectedCount }}</div>
      </el-card>
      <el-card shadow="never">
        <div class="summary-label">涉及节点</div>
        <div class="summary-value">{{ nodeCount }}</div>
      </el-card>
    </div>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>我的已办审批</span>
          <el-button @click="loadHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <div class="toolbar">
        <el-select v-model="filters.nodeType" clearable placeholder="全部节点" style="width: 160px">
          <el-option v-for="node in nodeOptions" :key="node" :label="node" :value="node" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width: 160px">
          <el-option label="已完成" value="completed" />
          <el-option label="已驳回" value="returned" />
          <el-option label="审批中" value="active" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="搜索节点、版本、意见"
          style="width: 260px"
        />
      </div>

      <el-table :data="filteredHistories" v-loading="loading" style="width: 100%">
        <el-table-column prop="node_type" label="节点" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.node_type }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="version" label="版本" width="90">
          <template #default="{ row }">V{{ row.version }}</template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>

        <el-table-column label="最近处理" width="170">
          <template #default="{ row }">{{ getLastHandledTime(row) }}</template>
        </el-table-column>

        <el-table-column label="审批记录" min-width="240">
          <template #default="{ row }">
            <div class="step-list">
              <el-tag
                v-for="step in row.steps"
                :key="stepKey(row.id, step)"
                :type="getStepStatusType(step.step_status)"
                size="small"
              >
                {{ step.step_order }}. {{ getStepText(step.step_status) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!filteredHistories.length && !loading" description="暂无已办记录">
        <el-button plain @click="loadHistory">重新检查</el-button>
      </el-empty>
    </el-card>

    <el-dialog v-model="detailVisible" title="已办审批详情" width="760px">
      <div v-if="currentInstance" class="detail-body">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="节点">{{ currentInstance.node_type }}</el-descriptions-item>
          <el-descriptions-item label="版本">V{{ currentInstance.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentInstance.status)">{{ getStatusText(currentInstance.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentInstance.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4>审批流转记录</h4>
        <el-timeline>
          <el-timeline-item
            v-for="step in currentInstance.steps"
            :key="stepKey(currentInstance.id, step)"
            :timestamp="step.completed_at ? formatTime(step.completed_at) : ''"
            :type="getTimelineType(step.step_status)"
          >
            <div class="timeline-row">
              <strong>第 {{ step.step_order }} 步</strong>
              <el-tag :type="getStepStatusType(step.step_status)" size="small">
                {{ getStepText(step.step_status) }}
              </el-tag>
            </div>
            <div v-if="step.opinion" class="opinion">审批意见：{{ step.opinion }}</div>
            <div v-else class="opinion muted">暂无审批意见</div>
          </el-timeline-item>
        </el-timeline>
      </div>
      <template #footer>
        <el-button type="primary" @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { approvalApi } from '@/api'

interface ApprovalStep {
  id?: number
  step_order: number
  step_status: string
  opinion?: string
  completed_at?: string | null
}

interface ApprovalInstance {
  id: number
  node_type: string
  version: number
  status: string
  steps: ApprovalStep[]
  created_at: string
  completed_at?: string | null
}

const loading = ref(false)
const histories = ref<ApprovalInstance[]>([])
const detailVisible = ref(false)
const currentInstance = ref<ApprovalInstance | null>(null)
const filters = reactive({
  nodeType: '',
  status: '',
  keyword: '',
})

const nodeOptions = computed(() => Array.from(new Set(histories.value.map((item) => item.node_type))).sort())
const nodeCount = computed(() => nodeOptions.value.length)
const approvedCount = computed(() => histories.value.filter((item) => item.steps.some((step) => step.step_status === 'approved')).length)
const rejectedCount = computed(() => histories.value.filter((item) => item.steps.some((step) => step.step_status === 'rejected') || item.status === 'returned').length)

const filteredHistories = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return histories.value.filter((item) => {
    const matchNode = !filters.nodeType || item.node_type === filters.nodeType
    const matchStatus = !filters.status || item.status === filters.status
    const matchKeyword = !keyword || [
      item.node_type,
      `v${item.version}`,
      getStatusText(item.status),
      ...item.steps.flatMap((step) => [getStepText(step.step_status), step.opinion || '']),
    ].some((text) => text.toLowerCase().includes(keyword))
    return matchNode && matchStatus && matchKeyword
  })
})

async function loadHistory() {
  loading.value = true
  try {
    histories.value = ((await approvalApi.getMyHistory(100)) as ApprovalInstance[]) || []
  } catch (e) {
    console.error('Failed to load approval history:', e)
  } finally {
    loading.value = false
  }
}

async function openDetail(instance: ApprovalInstance) {
  try {
    currentInstance.value = (await approvalApi.getInstance(instance.id)) as ApprovalInstance
    detailVisible.value = true
  } catch (e) {
    console.error('Failed to load approval detail:', e)
  }
}

function stepKey(instanceId: number, step: ApprovalStep): string {
  return `${instanceId}-${step.id || step.step_order}`
}

function getLastHandledTime(instance: ApprovalInstance): string {
  const handledTimes = instance.steps
    .map((step) => step.completed_at)
    .filter(Boolean) as string[]
  if (!handledTimes.length) return instance.completed_at ? formatTime(instance.completed_at) : '-'
  return formatTime(handledTimes.sort().at(-1) || handledTimes[0])
}

function getStatusType(status: string): '' | 'success' | 'warning' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger'> = {
    active: 'warning',
    completed: 'success',
    returned: 'danger',
  }
  return map[status] || ''
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    active: '审批中',
    completed: '已完成',
    returned: '已驳回',
  }
  return map[status] || status
}

function getStepStatusType(status: string): '' | 'success' | 'warning' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger'> = {
    approved: 'success',
    rejected: 'danger',
    pending: 'warning',
  }
  return map[status] || ''
}

function getStepText(status: string): string {
  const map: Record<string, string> = {
    approved: '已通过',
    rejected: '已驳回',
    pending: '待处理',
  }
  return map[status] || status
}

function getTimelineType(status: string): 'success' | 'warning' | 'danger' | 'primary' {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'primary'> = {
    approved: 'success',
    rejected: 'danger',
    pending: 'warning',
  }
  return map[status] || 'primary'
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

function formatTime(dateStr: string): string {
  return dayjs(dateStr).format('MM-DD HH:mm')
}

onMounted(loadHistory)
</script>

<style scoped>
.history-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-label {
  color: #606266;
  font-size: 13px;
}

.summary-value {
  margin-top: 8px;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.summary-value.success {
  color: #67c23a;
}

.summary-value.danger {
  color: #f56c6c;
}

.card-header,
.toolbar,
.timeline-row {
  display: flex;
  align-items: center;
}

.card-header {
  justify-content: space-between;
}

.toolbar {
  gap: 12px;
  margin-bottom: 16px;
}

.step-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-body h4 {
  margin: 18px 0 12px;
}

.timeline-row {
  gap: 8px;
}

.opinion {
  margin-top: 6px;
  color: #606266;
  line-height: 1.5;
}

.opinion.muted {
  color: #909399;
}

@media (max-width: 1000px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
