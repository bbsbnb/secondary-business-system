<template>
  <div class="contract-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>M24: 建造合同3张表关联</span>
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="选择月份"
            value-format="YYYY-MM"
            @change="loadContractData"
          />
        </div>
      </template>

      <!-- 3 Tables -->
      <el-row :gutter="20">
        <!-- Table 1: 预计总收入调整 -->
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>
              <div class="table-header">
                <span>表1: 预计总收入调整</span>
                <el-tag size="small">M8/M9/M10</el-tag>
              </div>
            </template>
            
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="原合同价">{{ formatMoney(contract?.original_contract_amount) }}</el-descriptions-item>
              <el-descriptions-item label="签证累计">
                <el-input-number v-model="form.visa_amount" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="索赔累计">
                <el-input-number v-model="form.claim_amount" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="变更累计">
                <el-input-number v-model="form.change_amount" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="合计" font-size="bold">
                {{ formatMoney(contract?.total_revenue || 0) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- Table 2: 总成本动态调整 -->
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>
              <div class="table-header">
                <span>表2: 总成本动态调整</span>
                <el-tag size="small">M11/M13</el-tag>
              </div>
            </template>
            
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="验工累计">
                <el-input-number v-model="form.verified_amount" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="消耗量累计">
                <el-input-number v-model="form.consumption_amount" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="材料结算累计">
                <el-input-number v-model="form.material_settlement" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="合计" font-size="bold">
                {{ formatMoney(contract?.total_cost || 0) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- Table 3: 总成本调整汇总 -->
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>
              <div class="table-header">
                <span>表3: 总成本调整汇总</span>
                <el-tag size="small">汇总</el-tag>
              </div>
            </template>
            
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="成本调整汇总">
                <el-input-number v-model="form.cost_adjustment_summary" :precision="2" size="small" style="width: 150px;" />
              </el-descriptions-item>
              <el-descriptions-item label="利润">
                {{ formatMoney(contract?.profit_amount || 0) }}
              </el-descriptions-item>
              <el-descriptions-item label="利润率">
                {{ contract?.profit_ratio || 0 }}%
              </el-descriptions-item>
              <el-descriptions-item label="超概状态">
                <el-tag v-if="contract?.over_budget" type="danger">超概 ⚠️</el-tag>
                <el-tag v-else type="success">正常</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- T6 超概说明 -->
      <el-alert
        v-if="contract?.over_budget && !contract.over_budget_explanation"
        title="T6: 超概预警 - 请在3日内提交超概说明"
        type="error"
        show-icon
        closable
        style="margin-top: 20px;"
      >
        <template #default>
          <el-input
            v-model="form.over_budget_explanation"
            type="textarea"
            :rows="3"
            placeholder="请输入超概说明..."
          />
        </template>
      </el-alert>

      <!-- Actions -->
      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="saveContract">保存数据</el-button>
        <el-button @click="autoAggregate">自动聚合数据</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { contractApi } from '@/api'
import { ElMessage } from 'element-plus'

const selectedMonth = ref(dayjs().format('YYYY-MM'))
const contract = ref<any>(null)
const form = ref({
  visa_amount: 0,
  claim_amount: 0,
  change_amount: 0,
  verified_amount: 0,
  consumption_amount: 0,
  material_settlement: 0,
  cost_adjustment_summary: 0,
  over_budget_explanation: '',
})

async function loadContractData() {
  try {
    const projectId = getCurrentProjectId()
    const data = await contractApi.get(projectId, selectedMonth.value)
    contract.value = data
    
    // Populate form
    if (data) {
      form.value = {
        visa_amount: Number(data.visa_amount || 0),
        claim_amount: Number(data.claim_amount || 0),
        change_amount: Number(data.change_amount || 0),
        verified_amount: Number(data.verified_amount || 0),
        consumption_amount: Number(data.consumption_amount || 0),
        material_settlement: Number(data.material_settlement || 0),
        cost_adjustment_summary: Number(data.cost_adjustment_summary || 0),
        over_budget_explanation: data.over_budget_explanation || '',
      }
    }
  } catch (e) {
    console.error('Failed to load contract:', e)
  }
}

async function saveContract() {
  try {
    const projectId = getCurrentProjectId()
    await contractApi.update(projectId, selectedMonth.value, form.value)
    ElMessage.success('保存成功')
    await loadContractData()
  } catch (e: any) {
    ElMessage.error(e.detail || '保存失败')
  }
}

async function autoAggregate() {
  try {
    const projectId = getCurrentProjectId()
    const data = await contractApi.createOrUpdate(projectId, selectedMonth.value)
    contract.value = data
    ElMessage.success('数据已自动聚合')
  } catch (e: any) {
    ElMessage.error(e.detail || '聚合失败')
  }
}

function formatMoney(value: number | null): string {
  if (!value) return '-'
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value)
}

function getCurrentProjectId(): number {
  return parseInt(localStorage.getItem('currentProjectId') || '0')
}

onMounted(() => {
  loadContractData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
