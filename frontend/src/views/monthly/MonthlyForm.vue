<template>
  <div class="monthly-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <span class="card-title">{{ nodeMeta.title }}</span>
            <p>{{ nodeMeta.description }}</p>
          </div>
          <el-tag type="primary">{{ nodeType }}</el-tag>
        </div>
      </template>

      <el-alert
        v-if="!supportedNode"
        title="该节点暂未配置表单"
        type="info"
        show-icon
        :closable="false"
      />

      <el-form v-else :model="form" label-width="128px" v-loading="loading">
        <template v-if="nodeType === 'M1'">
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <el-form-item label="中标合同价">
                <el-input-number v-model="form.contract_price" :min="0" :precision="2" controls-position="right" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="利润留存点">
                <el-input-number v-model="form.profit_retention_pct" :min="0" :max="100" :precision="2" controls-position="right" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="标后成本说明">
            <el-input v-model="form.post_bid_cost_note" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="不平衡报价策略">
            <el-input v-model="form.unbalanced_bidding_strategy" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="合同关键条款">
            <el-input v-model="form.key_contract_terms" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="总进度计划">
            <el-input v-model="form.master_schedule" type="textarea" :rows="3" />
          </el-form-item>
        </template>

        <template v-else>
          <el-row :gutter="20">
            <el-col v-for="field in nodeMeta.fields" :key="field.key" :xs="24" :md="field.type === 'textarea' ? 24 : 12">
              <el-form-item :label="field.label">
                <el-input
                  v-if="field.type === 'text'"
                  v-model="form[field.key]"
                  :placeholder="field.placeholder"
                />
                <el-input
                  v-else-if="field.type === 'textarea'"
                  v-model="form[field.key]"
                  type="textarea"
                  :rows="3"
                  :placeholder="field.placeholder"
                />
                <el-input-number
                  v-else-if="field.type === 'number'"
                  v-model="form[field.key]"
                  :min="0"
                  :precision="2"
                  controls-position="right"
                />
                <el-date-picker
                  v-else-if="field.type === 'date'"
                  v-model="form[field.key]"
                  type="date"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <el-form-item label="附件">
          <el-upload
            action="#"
            multiple
            :auto-upload="false"
            :file-list="attachments"
            @change="handleAttachmentChange"
            @remove="handleAttachmentRemove"
          >
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>

        <el-divider />

        <div class="action-bar">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" :loading="saving" @click="saveDraft">保存草稿</el-button>
          <el-button type="success" :loading="submitting" @click="submitForm">提交审批</el-button>
          <template v-if="nodeType === 'M1'">
            <el-button type="warning" :disabled="isLocked" @click="lockBaseline">锁定基线</el-button>
            <el-button :disabled="!isLocked" @click="unlockBaseline">申请解锁</el-button>
          </template>
        </div>
      </el-form>
    </el-card>

    <el-card v-if="instanceId" class="approval-card" shadow="never">
      <template #header>审批进度</template>
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step
          v-for="(step, index) in steps"
          :key="step.id || index"
          :title="getStepTitle(step, index)"
          :description="getStepDescription(step)"
          :status="getStepStatus(step, index)"
        />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { approvalApi, baselineApi, formApi } from '@/api'

type FieldType = 'text' | 'textarea' | 'number' | 'date'

interface NodeField {
  key: string
  label: string
  type: FieldType
  placeholder?: string
}

interface NodeMeta {
  title: string
  description: string
  fields: NodeField[]
}

const route = useRoute()
const nodeType = computed(() => String(route.params.nodeType || 'M1'))
const supportedNodes = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12', 'M13', 'M24', 'M25']
const supportedNode = computed(() => supportedNodes.includes(nodeType.value))

const loading = ref(false)
const saving = ref(false)
const submitting = ref(false)
const isLocked = ref(false)
const businessFormId = ref<number | null>(null)
const instanceId = ref<number | null>(null)
const currentStep = ref(0)
const steps = ref<any[]>([])
const attachments = ref<any[]>([])
const form = ref<Record<string, any>>({})

const nodeMetas: Record<string, NodeMeta> = {
  M1: {
    title: 'M1 基线录入',
    description: '录入合同价、标后成本、利润留存目标和总进度计划，形成项目经营基线。',
    fields: [],
  },
  M2: {
    title: 'M2 任务分解',
    description: '拆解月度施工、材料、资金和责任计划，作为后续执行依据。',
    fields: [
      { key: 'month', label: '计划月份', type: 'date' },
      { key: 'construction_plan', label: '施工计划', type: 'textarea', placeholder: '填写主要施工任务、工程量和完成节点' },
      { key: 'material_plan', label: '材料计划', type: 'textarea', placeholder: '填写主要材料需求、到场时间和责任人' },
      { key: 'fund_plan', label: '资金计划', type: 'textarea', placeholder: '填写付款、回款和资金缺口安排' },
      { key: 'owner', label: '责任人', type: 'text' },
    ],
  },
  M3: {
    title: 'M3 策划编制',
    description: '形成二次经营策划草案，明确签证、索赔、变更和资料支撑路径。',
    fields: [
      { key: 'strategy_theme', label: '策划主题', type: 'text' },
      { key: 'visa_opportunity', label: '签证机会', type: 'textarea' },
      { key: 'claim_opportunity', label: '索赔机会', type: 'textarea' },
      { key: 'change_opportunity', label: '变更机会', type: 'textarea' },
      { key: 'expected_amount', label: '预计金额', type: 'number' },
      { key: 'supporting_materials', label: '支撑资料', type: 'textarea' },
    ],
  },
  M4: {
    title: 'M4 策划审核',
    description: '对 M3 策划进行项目、工程、造价和经营维度审核。',
    fields: [
      { key: 'review_target', label: '审核对象', type: 'text' },
      { key: 'technical_review', label: '技术意见', type: 'textarea' },
      { key: 'cost_review', label: '造价意见', type: 'textarea' },
      { key: 'risk_points', label: '风险点', type: 'textarea' },
      { key: 'decision', label: '审核结论', type: 'text', placeholder: '通过 / 修改后通过 / 退回' },
    ],
  },
  M5: {
    title: 'M5 回款落实',
    description: '跟踪产值确认、开票、回款计划和逾期风险。',
    fields: [
      { key: 'receivable_amount', label: '应收金额', type: 'number' },
      { key: 'invoiced_amount', label: '已开票金额', type: 'number' },
      { key: 'received_amount', label: '已回款金额', type: 'number' },
      { key: 'planned_collection_date', label: '计划回款日', type: 'date' },
      { key: 'collection_risk', label: '回款风险', type: 'textarea' },
      { key: 'follow_up_action', label: '跟进措施', type: 'textarea' },
    ],
  },
  M6: {
    title: 'M6 认质认价',
    description: '记录材料规格、询价结果、核价依据和审批结论。',
    fields: [
      { key: 'material_name', label: '材料名称', type: 'text' },
      { key: 'specification', label: '规格型号', type: 'text' },
      { key: 'supplier', label: '供应商', type: 'text' },
      { key: 'budget_unit_price', label: '预算单价', type: 'number' },
      { key: 'unit_price', label: '申报单价', type: 'number' },
      { key: 'quantity', label: '数量', type: 'number' },
      { key: 'pricing_basis', label: '核价依据', type: 'textarea' },
    ],
  },
  M7: {
    title: 'M7 工作联系单',
    description: '记录现场联系事项、涉及图纸、责任单位和处理时限，形成后续签证或变更依据。',
    fields: [
      { key: 'contact_no', label: '联系单编号', type: 'text', placeholder: '可留空，由系统或线下编号补充' },
      { key: 'submit_date', label: '提交日期', type: 'date' },
      { key: 'subject', label: '联系主题', type: 'text' },
      { key: 'reason', label: '事由说明', type: 'textarea', placeholder: '描述现场问题、发起原因和期望处理结果' },
      { key: 'drawings', label: '涉及图纸', type: 'text', placeholder: '填写图纸编号或资料名称' },
      { key: 'responsible_party', label: '责任单位', type: 'text' },
      { key: 'required_finish_date', label: '要求完成日', type: 'date' },
    ],
  },
  M8: {
    title: 'M8 签证执行',
    description: '跟踪工程签证事项的类型、关联联系单、金额、依据和现场说明。',
    fields: [
      { key: 'visa_no', label: '签证编号', type: 'text', placeholder: '可留空，由系统或线下编号补充' },
      { key: 'visa_type', label: '签证类型', type: 'text', placeholder: '技术类 / 经济类 / 工期类' },
      { key: 'related_contact', label: '关联联系单', type: 'text', placeholder: '填写 M7 联系单编号或事项' },
      { key: 'amount', label: '签证金额', type: 'number' },
      { key: 'occurred_date', label: '发生日期', type: 'date' },
      { key: 'description', label: '签证说明', type: 'textarea' },
      { key: 'evidence', label: '支撑依据', type: 'textarea', placeholder: '现场照片、会议纪要、图纸、工程量确认等' },
    ],
  },
  M9: {
    title: 'M9 索赔执行',
    description: '记录索赔事件、合同依据、金额测算和责任划分，支撑索赔审批与归档。',
    fields: [
      { key: 'claim_no', label: '索赔编号', type: 'text', placeholder: '可留空，由系统或线下编号补充' },
      { key: 'claim_type', label: '索赔类型', type: 'text', placeholder: '工期 / 费用 / 综合' },
      { key: 'event_date', label: '事件日期', type: 'date' },
      { key: 'claim_amount', label: '索赔金额', type: 'number' },
      { key: 'delay_days', label: '影响天数', type: 'number' },
      { key: 'contract_basis', label: '合同依据', type: 'textarea' },
      { key: 'event_description', label: '事件说明', type: 'textarea' },
    ],
  },
  M10: {
    title: 'M10 设计变更',
    description: '记录设计变更来源、影响范围、成本测算和实施安排。',
    fields: [
      { key: 'change_no', label: '变更编号', type: 'text' },
      { key: 'change_source', label: '变更来源', type: 'text', placeholder: '业主 / 设计 / 现场 / 其他' },
      { key: 'received_date', label: '接收日期', type: 'date' },
      { key: 'estimated_amount', label: '预计金额', type: 'number' },
      { key: 'affected_scope', label: '影响范围', type: 'textarea' },
      { key: 'cost_review', label: '成本审核', type: 'textarea' },
      { key: 'implementation_plan', label: '实施安排', type: 'textarea' },
    ],
  },
  M11: {
    title: 'M11 月验工计价',
    description: '汇总月度验工产值、扣减项、申报金额和审核意见。',
    fields: [
      { key: 'valuation_month', label: '计价月份', type: 'date' },
      { key: 'reported_output', label: '申报产值', type: 'number' },
      { key: 'verified_output', label: '核定产值', type: 'number' },
      { key: 'deduction_amount', label: '扣减金额', type: 'number' },
      { key: 'payment_ratio', label: '付款比例', type: 'number' },
      { key: 'quantity_summary', label: '工程量摘要', type: 'textarea' },
      { key: 'review_notes', label: '审核意见', type: 'textarea' },
    ],
  },
  M12: {
    title: 'M12 材料结算',
    description: '记录材料供应、验收、结算金额和扣款调整情况。',
    fields: [
      { key: 'settlement_no', label: '结算编号', type: 'text' },
      { key: 'supplier', label: '供应商', type: 'text' },
      { key: 'material_category', label: '材料类别', type: 'text' },
      { key: 'settlement_amount', label: '结算金额', type: 'number' },
      { key: 'deduction_amount', label: '扣款金额', type: 'number' },
      { key: 'acceptance_date', label: '验收日期', type: 'date' },
      { key: 'settlement_basis', label: '结算依据', type: 'textarea' },
    ],
  },
  M13: {
    title: 'M13 消耗核定',
    description: '核定月度材料消耗、预算差异和纠偏措施。',
    fields: [
      { key: 'material_name', label: '材料名称', type: 'text' },
      { key: 'budget_consumption', label: '预算消耗', type: 'number' },
      { key: 'actual_consumption', label: '实际消耗', type: 'number' },
      { key: 'variance_amount', label: '偏差数量', type: 'number' },
      { key: 'variance_reason', label: '偏差原因', type: 'textarea' },
      { key: 'correction_action', label: '纠偏措施', type: 'textarea' },
      { key: 'responsible_owner', label: '责任人', type: 'text' },
    ],
  },
  M24: {
    title: 'M24 建造合同',
    description: '汇总收入、成本、利润和超概说明，形成建造合同月度数据枢纽。',
    fields: [
      { key: 'contract_month', label: '合同月份', type: 'date' },
      { key: 'original_contract_amount', label: '原合同价', type: 'number' },
      { key: 'visa_amount', label: '签证累计', type: 'number' },
      { key: 'claim_amount', label: '索赔累计', type: 'number' },
      { key: 'change_amount', label: '变更累计', type: 'number' },
      { key: 'verified_amount', label: '验工累计', type: 'number' },
      { key: 'material_settlement', label: '材料结算', type: 'number' },
      { key: 'over_budget_explanation', label: '超概说明', type: 'textarea' },
    ],
  },
  M25: {
    title: 'M25 月度复盘',
    description: '沉淀本月经营结果、问题闭环、风险预警和下月改进计划。',
    fields: [
      { key: 'review_month', label: '复盘月份', type: 'date' },
      { key: 'revenue_summary', label: '收入总结', type: 'textarea' },
      { key: 'cost_summary', label: '成本总结', type: 'textarea' },
      { key: 'cash_collection_summary', label: '回款总结', type: 'textarea' },
      { key: 'key_issues', label: '关键问题', type: 'textarea' },
      { key: 'risk_warnings', label: '风险预警', type: 'textarea' },
      { key: 'next_month_actions', label: '下月措施', type: 'textarea' },
      { key: 'owner', label: '责任人', type: 'text' },
    ],
  },
}

const nodeMeta = computed(() => nodeMetas[nodeType.value] || {
  title: nodeType.value,
  description: '该节点暂未配置表单。',
  fields: [],
})

function createDefaultForm() {
  if (nodeType.value === 'M1') {
    return {
      contract_price: 0,
      profit_retention_pct: 8,
      post_bid_cost_note: '',
      unbalanced_bidding_strategy: '',
      key_contract_terms: '',
      master_schedule: '',
    }
  }

  return nodeMeta.value.fields.reduce<Record<string, any>>((result, field) => {
    result[field.key] = field.type === 'number' ? 0 : field.type === 'date' ? dayjs().format('YYYY-MM-DD') : ''
    return result
  }, {})
}

async function loadNodeData() {
  if (!supportedNode.value) return
  loading.value = true
  form.value = createDefaultForm()
  businessFormId.value = null
  instanceId.value = null
  steps.value = []

  try {
    if (nodeType.value === 'M1') {
      await loadBaseline()
    } else {
      await loadLatestBusinessForm()
    }
  } finally {
    loading.value = false
  }
}

async function loadBaseline() {
  try {
    const data = await baselineApi.get(getCurrentProjectId())
    form.value = {
      ...form.value,
      contract_price: Number(data.contract_price || 0),
      profit_retention_pct: Number(data.profit_retention_pct || 8),
      post_bid_cost_note: data.post_bid_cost?.note || '',
      unbalanced_bidding_strategy: data.unbalanced_bidding_strategy || '',
      key_contract_terms: data.key_contract_terms || '',
      master_schedule: data.master_schedule || '',
    }
    isLocked.value = Boolean(data.locked)
  } catch (error: any) {
    if (error.response?.status !== 404) {
      console.error('Failed to load baseline:', error)
    }
    isLocked.value = false
  }
}

async function loadLatestBusinessForm() {
  try {
    const data = await formApi.list({ node_type: nodeType.value, project_id: getCurrentProjectId(), page_size: 1 })
    const latest = Array.isArray(data) ? data[0] : null
    if (!latest) return
    businessFormId.value = latest.id
    form.value = { ...form.value, ...(latest.form_data || {}) }
  } catch (error) {
    console.error('Failed to load monthly form:', error)
  }
}

async function saveDraft() {
  if (nodeType.value === 'M1') {
    await saveBaseline()
    return
  }

  saving.value = true
  try {
    const payload = buildBusinessPayload()
    if (businessFormId.value) {
      const data = await formApi.update(businessFormId.value, { form_data: payload.form_data, attachments: [] })
      businessFormId.value = data.id
    } else {
      const data = await formApi.create(payload)
      businessFormId.value = data.id
    }
    ElMessage.success('草稿已保存')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveBaseline() {
  saving.value = true
  try {
    await baselineApi.create(getCurrentProjectId(), {
      contract_price: form.value.contract_price,
      profit_retention_pct: form.value.profit_retention_pct,
      post_bid_cost: { note: form.value.post_bid_cost_note },
      unbalanced_bidding_strategy: form.value.unbalanced_bidding_strategy,
      key_contract_terms: form.value.key_contract_terms,
      master_schedule: form.value.master_schedule,
    })
    ElMessage.success('基线数据已保存')
    await loadBaseline()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submitForm() {
  if (nodeType.value === 'M1') {
    await saveBaseline()
    ElMessage.success('M1 基线已保存，可按需锁定')
    return
  }

  submitting.value = true
  try {
    if (!businessFormId.value) {
      await saveDraft()
    }
    if (!businessFormId.value) return

    const instance = await approvalApi.createInstance({
      node_type: nodeType.value,
      business_form_id: businessFormId.value,
      initiator_id: getCurrentUserId(),
    })
    instanceId.value = instance.id
    currentStep.value = instance.current_step || 1
    steps.value = []
    ElMessage.success('已提交审批')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function lockBaseline() {
  try {
    await ElMessageBox.confirm('锁定后基线数据不可直接修改，确认锁定吗？', '确认锁定', { type: 'warning' })
    await baselineApi.lock(getCurrentProjectId(), { confirmed: true })
    isLocked.value = true
    ElMessage.success('基线已锁定')
  } catch {}
}

async function unlockBaseline() {
  try {
    const { value } = await ElMessageBox.prompt('请输入解锁原因', '解锁申请', {
      inputType: 'textarea',
      inputPlaceholder: '说明需要调整基线的原因',
    })
    if (!value) return
    await baselineApi.unlock(getCurrentProjectId(), { reason: value, approver_id: getCurrentUserId() })
    isLocked.value = false
    ElMessage.success('基线已解锁')
  } catch {}
}

function buildBusinessPayload() {
  return {
    project_id: getCurrentProjectId(),
    node_type: nodeType.value,
    template_type: nodeType.value,
    form_data: { ...form.value },
  }
}

function resetForm() {
  form.value = createDefaultForm()
  attachments.value = []
}

function handleAttachmentChange(file: any) {
  attachments.value.push(file)
}

function handleAttachmentRemove(file: any) {
  attachments.value = attachments.value.filter((item) => item.uid !== file.uid)
}

function getStepTitle(step: any, index: number): string {
  return step.step_order ? `第 ${step.step_order} 步` : `第 ${index + 1} 步`
}

function getStepDescription(step: any): string {
  return step.department_name || step.step_status || '待处理'
}

function getStepStatus(step: any, index: number): 'success' | 'process' | 'wait' | 'error' {
  if (step.step_status === 'approved') return 'success'
  if (step.step_status === 'rejected') return 'error'
  if (index + 1 === currentStep.value) return 'process'
  return 'wait'
}

function getCurrentProjectId(): number {
  return Number(localStorage.getItem('currentProjectId') || '0')
}

function getCurrentUserId(): number {
  const userStr = localStorage.getItem('user')
  if (!userStr) return 0
  try {
    return JSON.parse(userStr).id || 0
  } catch {
    return 0
  }
}

watch(nodeType, () => {
  loadNodeData()
})

onMounted(() => {
  loadNodeData()
})
</script>

<style scoped>
.monthly-form {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-title {
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.card-header p {
  margin: 6px 0 0;
  color: #606266;
  font-size: 13px;
}

.action-bar {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.approval-card {
  margin-top: 16px;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-date-editor) {
  width: 100%;
}
</style>
