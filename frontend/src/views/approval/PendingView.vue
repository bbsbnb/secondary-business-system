<template>
  <div class="pending-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的待办审批</span>
          <el-button type="primary" @click="refresh">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <el-table :data="approvals" v-loading="loading" style="width: 100%">
        <el-table-column prop="node_type" label="节点" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.node_type }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="version" label="版本" width="70" />
        
        <el-table-column label="当前步骤" min-width="200">
          <template #default="{ row }">
            <div v-for="step in row.steps" :key="step.id" style="margin-bottom: 4px;">
              <el-tag 
                :type="getStepStatusType(step.step_status)" 
                size="small"
                effect="dark"
                v-if="step.step_status !== 'pending'"
              >
                {{ step.step_order }}. {{ getDeptName(step) }} {{ step.opinion ? '✓' : '' }}
              </el-tag>
              <el-tag type="warning" size="small" v-else effect="plain">
                ⏳ {{ step.step_order }}. 待处理
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!approvals.length && !loading" description="暂无待办审批" />
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="审批详情" width="700px">
      <div v-if="currentInstance">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="节点">{{ currentInstance.node_type }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ currentInstance.version }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentInstance.status)">
              {{ getStatusText(currentInstance.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentInstance.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 16px;">审批步骤</h4>
        <el-timeline>
          <el-timeline-item
            v-for="step in currentInstance.steps"
            :key="step.id"
            :timestamp="step.completed_at ? formatTime(step.completed_at) : ''"
            :type="getStepColor(step.step_status)"
          >
            <p><strong>第{{ step.step_order }}步</strong> - {{ getDeptName(step) }}</p>
            <p v-if="step.opinion" style="color: #666; margin-top: 4px;">{{ step.opinion }}</p>
            <el-tag v-if="step.step_status === 'pending'" type="warning" size="small">等待处理</el-tag>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { approvalApi } from '@/api'
import type { ApprovalInstanceResponse } from '@/api'

const loading = ref(false)
const approvals = ref<any[]>([])
const detailVisible = ref(false)
const currentInstance = ref<any>(null)

async function refresh() {
  loading.value = true
  try {
    const data = await approvalApi.myPending()
    approvals.value = data || []
  } catch (e) {
    console.error('Failed to load pending:', e)
  } finally {
    loading.value = false
  }
}

function openDetail(instance: any) {
  currentInstance.value = instance
  detailVisible.value = true
}

function getStepStatusType(status: string): string {
  const map: Record<string, string> = {
    approved: 'success',
    rejected: 'danger',
    pending: 'warning',
  }
  return map[status] || ''
}

function getDeptName(step: any): string {
  // Simplified - in real app would fetch department name
  return `步骤 ${step.step_order}`
}

function getStatusType(status: string): string {
  const map: Record<string, string> = {
    active: '',
    completed: 'success',
    returned: 'warning',
  }
  return map[status] || ''
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    active: '进行中',
    completed: '已完成',
    returned: '已退回',
  }
  return map[status] || status
}

function getStepColor(status: string): string {
  const map: Record<string, string> = {
    approved: 'green',
    rejected: 'red',
    pending: 'orange',
  }
  return map[status] || ''
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

function formatTime(dateStr: string): string {
  return dayjs(dateStr).format('MM-DD HH:mm')
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
