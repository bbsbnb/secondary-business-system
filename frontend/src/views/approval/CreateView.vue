<template>
  <div class="create-view">
    <el-card>
      <template #header>
        <span>发起审批 - {{ nodeType }}</span>
      </template>

      <el-steps :active="currentStep" finish-status="success" style="margin-bottom: 30px;">
        <el-step title="选择节点" description="选择要发起的审批类型" />
        <el-step title="填写表单" description="填写业务数据" />
        <el-step title="确认提交" description="确认信息并提交" />
      </el-steps>

      <!-- Step 1: Select Node -->
      <div v-if="currentStep === 0">
        <h4>选择审批节点</h4>
        <el-table :data="availableNodes" style="width: 100%;" @row-click="selectNode">
          <el-table-column prop="node_type" label="节点代码" width="100" />
          <el-table-column prop="name" label="节点名称" min-width="200" />
          <el-table-column prop="description" label="说明" min-width="300" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                {{ row.enabled ? '可用' : '开发中' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Step 2: Fill Form -->
      <div v-if="currentStep === 1 && selectedNode">
        <h4>{{ selectedNode.name }} - 填写表单</h4>
        
        <!-- Dynamic form based on node type -->
        <el-form :model="formData" label-width="120px" v-if="selectedNode.node_type === 'M7'">
          <el-form-item label="联系单编号">
            <el-input v-model="formData.contact_no" placeholder="系统自动生成" disabled />
          </el-form-item>
          
          <el-form-item label="事由" required>
            <el-input v-model="formData.reason" type="textarea" :rows="3" />
          </el-form-item>
          
          <el-form-item label="涉及图纸">
            <el-input v-model="formData.drawings" placeholder="相关图纸编号" />
          </el-form-item>
          
          <el-form-item label="附件">
            <el-upload action="#" multiple :auto-upload="false" :file-list="fileList" @change="handleFileChange">
              <el-button type="default">选择文件</el-button>
            </el-upload>
          </el-form-item>
        </el-form>

        <el-form v-else-if="selectedNode.node_type === 'M8'">
          <el-form-item label="签证类型">
            <el-radio-group v-model="formData.visa_type">
              <el-radio-button label="technical">技术类</el-radio-button>
              <el-radio-button label="economic">经济类</el-radio-button>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item label="金额(元)">
            <el-input-number v-model="formData.amount" :precision="2" :min="0" />
          </el-form-item>
          
          <el-form-item label="说明">
            <el-input v-model="formData.description" type="textarea" :rows="4" />
          </el-form-item>
        </el-form>

        <div v-else>
          <el-alert title="该节点表单模板待完善" type="warning" show-icon />
        </div>

        <div style="margin-top: 20px;">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button type="primary" @click="currentStep = 2">下一步</el-button>
        </div>
      </div>

      <!-- Step 3: Confirm & Submit -->
      <div v-if="currentStep === 2">
        <h4>确认提交</h4>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="节点">{{ selectedNode?.name }}</el-descriptions-item>
          <el-descriptions-item label="编号">{{ formData.contact_no || '自动生成' }}</el-descriptions-item>
          <el-descriptions-item label="提交人">{{ userName }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ submitTime }}</el-descriptions-item>
        </el-descriptions>

        <div style="margin-top: 20px;">
          <el-button @click="currentStep = 1">上一步</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            提交审批
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { approvalApi, formApi } from '@/api'

const currentStep = ref(0)
const submitting = ref(false)
const fileList = ref<any[]>([])

const availableNodes = ref([
  { node_type: 'M2', name: '月度任务分解', description: '月施工进度计划、材料采购计划、资金计划', enabled: true },
  { node_type: 'M4', name: '二次经营策划审核', description: '项目经理→工程部→造价部→经营副总', enabled: true },
  { node_type: 'M6', name: '认质认价执行', description: '规格参数→询价→核价→编制→审批→签章', enabled: true },
  { node_type: 'M7', name: '工作联系单', description: '基础验证流程：编制→审核→核价→审批→签章→归档', enabled: true },
  { node_type: 'M8', name: '签证事项执行', description: '全系统最复杂流程，含印章路由和金额分支', enabled: true },
  { node_type: 'M9', name: '索赔价差执行', description: '双28天硬时限，含证据链检查', enabled: true },
  { node_type: 'M10', name: '设计变更执行', description: '变更通知→采购评估→成本审核→签章→归档', enabled: true },
  { node_type: 'M11', name: '月验工计价', description: '平行审核后串行审批，含超合同预警', enabled: true },
  { node_type: 'M12', name: '材料月结算', description: '编制→复核→审核→核价→审批→终审→签章', enabled: true },
  { node_type: 'M13', name: '月消耗量核定', description: '台账→审核→采供→财务→成本比对→归档', enabled: true },
])

const selectedNode = ref<any>(null)
const formData = ref({
  contact_no: '',
  reason: '',
  drawings: '',
  visa_type: 'technical',
  amount: 0,
  description: '',
})

const userName = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.real_name || ''
  } catch {
    return ''
  }
})

const submitTime = computed(() => dayjs().format('YYYY-MM-DD HH:mm'))

function selectNode(row: any) {
  if (!row.enabled) {
    ElMessage.warning('该节点暂不可用')
    return
  }
  selectedNode.value = row
  currentStep.value = 1
}

function handleFileChange(file: any) {
  fileList.value.push(file)
}

async function handleSubmit() {
  submitting.value = true
  try {
    // Create business form
    const formRes = await formApi.create({
      project_id: getCurrentProjectId(),
      node_type: selectedNode.value.node_type,
      form_data: formData.value,
    })

    // Create approval instance
    const instance = await approvalApi.createInstance({
      node_type: selectedNode.value.node_type,
      business_form_id: formRes.id,
      initiator_id: getCurrentUserId(),
    })

    ElMessage.success(`已提交${selectedNode.value.name}审批`)
    currentStep.value = 0
    selectedNode.value = null
    fileList.value = []
  } catch (e: any) {
    ElMessage.error(e.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

function getCurrentProjectId(): number {
  return parseInt(localStorage.getItem('currentProjectId') || '0')
}

function getCurrentUserId(): number {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return user.id || 0
  } catch {
    return 0
  }
}

onMounted(() => {
  // Auto-generate contact number
  formData.value.contact_no = `LXD-${dayjs().format('YYYYMMDD')}-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`
})
</script>

<style scoped>
.el-form-item {
  margin-bottom: 20px;
}
</style>
