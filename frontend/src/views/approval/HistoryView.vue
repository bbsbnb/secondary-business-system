<template>
  <div class="history-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的已办审批</span>
        </div>
      </template>

      <el-table :data="histories" v-loading="loading" style="width: 100%">
        <el-table-column prop="node_type" label="节点" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.node_type }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="version" label="版本" width="70" />
        
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="完成时间" width="160">
          <template #default="{ row }">
            {{ row.completed_at ? formatTime(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!histories.length && !loading" description="暂无已办记录" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { approvalApi } from '@/api'

const loading = ref(false)
const histories = ref<any[]>([])

async function loadHistory() {
  loading.value = true
  try {
    const data = await approvalApi.myHistory(50)
    histories.value = data || []
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    loading.value = false
  }
}

function getStatusType(status: string): string {
  return status === 'completed' ? 'success' : status === 'returned' ? 'warning' : ''
}

function getStatusText(status: string): string {
  return status === 'completed' ? '已完成' : status === 'returned' ? '已退回' : status
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

function formatTime(dateStr: string): string {
  return dayjs(dateStr).format('MM-DD HH:mm')
}

function openDetail(instance: any) {
  // Navigate to detail or show dialog
  console.log('View detail:', instance.id)
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
