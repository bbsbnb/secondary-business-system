<template>
  <div class="baseline-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>M1: 基线数据录入</span>
          <el-tag :type="isLocked ? 'warning' : 'success'">
            {{ isLocked ? '已锁定' : '未锁定' }}
          </el-tag>
        </div>
      </template>

      <el-form :model="form" label-width="120px" v-loading="loading">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="中标合同价">
              <el-input-number v-model="form.contract_price" :precision="2" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="利润留存点(%)">
              <el-input-number v-model="form.profit_retention_pct" :precision="2" :min="0" :max="100" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="标后成本(18张附表)">
          <el-upload
            action="#"
            :auto-upload="false"
            :file-list="costFiles"
            @change="handleCostUpload"
          >
            <el-button type="primary">上传标后成本表</el-button>
          </el-upload>
        </el-form-item>

        <el-form-item label="不平衡报价策略">
          <el-input v-model="form.unbalanced_bidding_strategy" type="textarea" :rows="3" />
        </el-form-item>

        <el-form-item label="合同关键条款">
          <el-input v-model="form.key_contract_terms" type="textarea" :rows="4" />
        </el-form-item>

        <el-form-item label="总进度计划">
          <el-input v-model="form.master_schedule" type="textarea" :rows="3" />
        </el-form-item>

        <el-form-item label="附件上传">
          <el-upload
            multiple
            action="#"
            :auto-upload="false"
            :file-list="attachments"
            @change="handleAttachmentChange"
          >
            <el-button type="default">选择文件</el-button>
          </el-upload>
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="saveBaseline">保存基线数据</el-button>
          <el-button 
            type="danger" 
            @click="lockBaseline" 
            :disabled="!isLocked"
          >
            锁定基线（不可逆）
          </el-button>
          <el-button 
            type="warning" 
            @click="unlockBaseline" 
            :disabled="isLocked"
          >
            申请解锁
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { baselineApi } from '@/api'

const loading = ref(false)
const isLocked = ref(false)
const form = ref({
  contract_price: null as number | null,
  post_bid_cost: null as any,
  profit_retention_pct: null as number | null,
  unbalanced_bidding_strategy: '',
  key_contract_terms: '',
  master_schedule: '',
})

const costFiles = ref<any[]>([])
const attachments = ref<any[]>([])

async function loadBaseline() {
  loading.value = true
  try {
    const projectId = getCurrentProjectId()
    const data = await baselineApi.get(projectId)
    if (data) {
      form.value = {
        contract_price: data.contract_price || null,
        post_bid_cost: data.post_bid_cost || null,
        profit_retention_pct: data.profit_retention_pct || null,
        unbalanced_bidding_strategy: data.unbalanced_bidding_strategy || '',
        key_contract_terms: data.key_contract_terms || '',
        master_schedule: data.master_schedule || '',
      }
      isLocked.value = data.locked || false
    }
  } catch (e) {
    console.error('Failed to load baseline:', e)
  } finally {
    loading.value = false
  }
}

async function saveBaseline() {
  loading.value = true
  try {
    const projectId = getCurrentProjectId()
    await baselineApi.create(projectId, form.value)
    ElMessage.success('基线数据已保存')
    await loadBaseline()
  } catch (e: any) {
    ElMessage.error(e.detail || '保存失败')
  } finally {
    loading.value = false
  }
}

async function lockBaseline() {
  try {
    await ElMessageBox.confirm(
      '锁定后基线数据将不可修改！如需修改需申请解锁并留痕。确定要锁定吗？',
      '确认锁定',
      { type: 'warning' }
    )
    
    const projectId = getCurrentProjectId()
    await baselineApi.lock(projectId, { confirmed: true })
    isLocked.value = true
    ElMessage.success('基线已锁定')
  } catch {}
}

async function unlockBaseline() {
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入解锁原因', '解锁申请', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPlaceholder: '解锁原因将永久记录',
      inputType: 'textarea',
    })
    
    if (!reason) return
    
    const projectId = getCurrentProjectId()
    await baselineApi.unlock(projectId, { reason, approver_id: getCurrentUserId() })
    isLocked.value = false
    ElMessage.success('基线已解锁')
  } catch {}
}

function handleCostUpload(file: any) {
  costFiles.value.push(file)
}

function handleAttachmentChange(file: any) {
  attachments.value.push(file)
}

function getCurrentProjectId(): number {
  // In real app, get from route params or store
  return parseInt(localStorage.getItem('currentProjectId') || '0')
}

function getCurrentUserId(): number {
  // In real app, get from user store
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      return user.id || 0
    } catch {}
  }
  return 0
}

onMounted(() => {
  loadBaseline()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
