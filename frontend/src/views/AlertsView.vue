<template>
  <div class="alerts-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>预警中心</span>
          <div>
            <el-select v-model="filterSeverity" placeholder="严重程度" clearable style="width: 120px; margin-right: 8px;">
              <el-option label="全部" value="" />
              <el-option label="严重" value="critical" />
              <el-option label="警告" value="warning" />
              <el-option label="提示" value="info" />
            </el-select>
            <el-button type="primary" @click="loadAlerts">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredAlerts" v-loading="loading" style="width: 100%">
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ row.alert_type }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="message" label="内容" min-width="300" show-overflow-tooltip />
        
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-icon :size="16" :color="getSeverityColor(row.severity)">
              <WarningFilled v-if="row.severity === 'critical'" />
              <Warning v-else-if="row.severity === 'warning'" />
              <InfoFilled v-else />
            </el-icon>
          </template>
        </el-table-column>
        
        <el-table-column label="已升级" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.escalated" type="danger" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="已解决" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.resolved" type="success" size="small">是</el-tag>
            <el-tag v-else type="warning" size="small">否</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatTimeAgo(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="success" 
              size="small" 
              :disabled="row.resolved"
              @click="resolveAlert(row.id)"
            >
              解决
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!filteredAlerts.length && !loading" description="暂无预警" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import { alertApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const alerts = ref<any[]>([])
const filterSeverity = ref('')

const filteredAlerts = computed(() => {
  if (!filterSeverity.value) return alerts.value
  return alerts.value.filter(a => a.severity === filterSeverity.value)
})

async function loadAlerts() {
  loading.value = true
  try {
    const data = await alertApi.list({ resolved: false })
    alerts.value = data || []
  } catch (e) {
    console.error('Failed to load alerts:', e)
  } finally {
    loading.value = false
  }
}

async function resolveAlert(alertId: number) {
  try {
    await alertApi.resolve(alertId)
    ElMessage.success('预警已标记为已解决')
    await loadAlerts()
  } catch (e: any) {
    ElMessage.error(e.detail || '操作失败')
  }
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

function formatTimeAgo(dateStr: string): string {
  return dayjs(dateStr).fromNow()
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
