<template>
  <div class="alerts-view">
    <el-row :gutter="16" class="stats-row">
      <el-col v-for="card in statCards" :key="card.label" :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-note">{{ card.note }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <span class="card-title">预警中心</span>
            <p>集中跟踪超时、超概、资料缺失和回款风险</p>
          </div>
          <div class="header-actions">
            <el-button @click="resetFilters">重置</el-button>
            <el-button @click="loadAlerts">刷新</el-button>
            <el-button type="primary" @click="showCreateDialog = true">新建预警</el-button>
          </div>
        </div>
      </template>

      <div class="toolbar">
        <el-select v-model="filters.severity" clearable placeholder="严重程度" style="width: 140px" @change="loadAlerts">
          <el-option label="严重" value="critical" />
          <el-option label="警告" value="warning" />
          <el-option label="提示" value="info" />
        </el-select>
        <el-select v-model="filters.alert_type" clearable placeholder="类型" style="width: 160px" @change="loadAlerts">
          <el-option label="超时预警" value="timeout" />
          <el-option label="超概预警" value="over_budget" />
          <el-option label="资料缺失" value="missing_document" />
          <el-option label="回款提醒" value="collection" />
          <el-option label="手动预警" value="manual" />
        </el-select>
        <el-select v-model="filters.resolved" placeholder="处理状态" style="width: 140px" @change="loadAlerts">
          <el-option label="未解决" :value="false" />
          <el-option label="已解决" :value="true" />
          <el-option label="全部" value="all" />
        </el-select>
      </div>

      <el-table :data="alerts" v-loading="loading" style="width: 100%">
        <el-table-column label="类型" width="130">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" effect="plain">{{ getAlertTypeLabel(row.alert_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="内容" min-width="320" show-overflow-tooltip />
        <el-table-column prop="node_type" label="节点" width="90" align="center">
          <template #default="{ row }">{{ row.node_type || '-' }}</template>
        </el-table-column>
        <el-table-column label="严重程度" width="110" align="center">
          <template #default="{ row }">
            <span class="severity" :style="{ color: getSeverityColor(row.severity) }">
              {{ getSeverityLabel(row.severity) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="已升级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.escalated ? 'danger' : 'info'" size="small">{{ row.escalated ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="已解决" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.resolved ? 'success' : 'warning'" size="small">{{ row.resolved ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="150">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link :disabled="row.resolved" @click="resolveAlert(row.id)">解决</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!alerts.length && !loading" description="暂无预警" />
    </el-card>

    <el-dialog v-model="showCreateDialog" title="新建预警" width="560px">
      <el-form :model="createForm" label-width="96px">
        <el-form-item label="类型" required>
          <el-select v-model="createForm.alert_type" style="width: 100%">
            <el-option label="超时预警" value="timeout" />
            <el-option label="超概预警" value="over_budget" />
            <el-option label="资料缺失" value="missing_document" />
            <el-option label="回款提醒" value="collection" />
            <el-option label="手动预警" value="manual" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度" required>
          <el-select v-model="createForm.severity" style="width: 100%">
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="提示" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="节点">
          <el-input v-model="createForm.node_type" placeholder="如 M11、M24，可选" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input v-model="createForm.message" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createAlert">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { ElMessage } from 'element-plus'
import { alertApi } from '@/api'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const loading = ref(false)
const creating = ref(false)
const alerts = ref<any[]>([])
const stats = ref<any>({ total: 0, unresolved: 0, critical: 0, warning: 0, by_type: {} })
const showCreateDialog = ref(false)

const filters = ref({
  severity: '',
  alert_type: '',
  resolved: false as boolean | 'all',
})

const createForm = ref({
  alert_type: 'manual',
  severity: 'warning',
  node_type: '',
  message: '',
})

const statCards = computed(() => [
  { label: '全部预警', value: stats.value.total || 0, note: '系统累计记录', color: '#409EFF' },
  { label: '未解决', value: stats.value.unresolved || 0, note: '需要继续跟进', color: '#E6A23C' },
  { label: '严重', value: stats.value.critical || 0, note: '优先处理', color: '#F56C6C' },
  { label: '警告', value: stats.value.warning || 0, note: '持续观察', color: '#909399' },
])

async function loadAlerts() {
  loading.value = true
  try {
    const params: Record<string, any> = { page_size: 50 }
    if (filters.value.severity) params.severity = filters.value.severity
    if (filters.value.alert_type) params.alert_type = filters.value.alert_type
    if (filters.value.resolved !== 'all') params.resolved = filters.value.resolved

    const [listData, statData] = await Promise.all([
      alertApi.list(params),
      alertApi.stats(),
    ])
    alerts.value = listData?.items || []
    stats.value = statData || stats.value
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '预警加载失败')
  } finally {
    loading.value = false
  }
}

async function createAlert() {
  if (!createForm.value.message.trim()) {
    ElMessage.warning('请填写预警内容')
    return
  }
  creating.value = true
  try {
    await alertApi.createManual({
      ...createForm.value,
      project_id: Number(localStorage.getItem('currentProjectId') || '1'),
    })
    ElMessage.success('预警已创建')
    showCreateDialog.value = false
    createForm.value = { alert_type: 'manual', severity: 'warning', node_type: '', message: '' }
    await loadAlerts()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function resolveAlert(alertId: number) {
  try {
    await alertApi.resolve(alertId)
    ElMessage.success('预警已标记为已解决')
    await loadAlerts()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '操作失败')
  }
}

function resetFilters() {
  filters.value = { severity: '', alert_type: '', resolved: false }
  loadAlerts()
}

function getSeverityType(severity: string): 'danger' | 'warning' | 'info' {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

function getSeverityColor(severity: string): string {
  const map: Record<string, string> = {
    critical: '#F56C6C',
    warning: '#E6A23C',
    info: '#909399',
  }
  return map[severity] || '#909399'
}

function getSeverityLabel(severity: string): string {
  const map: Record<string, string> = {
    critical: '严重',
    warning: '警告',
    info: '提示',
  }
  return map[severity] || severity
}

function getAlertTypeLabel(type: string): string {
  const map: Record<string, string> = {
    timeout: '超时预警',
    over_budget: '超概预警',
    missing_document: '资料缺失',
    collection: '回款提醒',
    manual: '手动预警',
  }
  return map[type] || type
}

function formatTime(dateStr: string): string {
  return dateStr ? dayjs(dateStr).fromNow() : '-'
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.alerts-view {
  padding: 20px;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  border-radius: 8px;
}

.stat-label,
.stat-note {
  color: #909399;
  font-size: 13px;
}

.stat-value {
  margin: 8px 0;
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-header p {
  margin: 6px 0 0;
  color: #606266;
  font-size: 13px;
}

.header-actions,
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar {
  margin-bottom: 16px;
}

.severity {
  font-weight: 600;
}
</style>
