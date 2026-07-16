<template>
  <div class="monthly-form">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ nodeTitle }}</span>
          <el-tag :type="nodeType === 'M7' ? '' : 'primary'">{{ nodeType }}</el-tag>
        </div>
      </template>

      <!-- Node-specific form content -->
      <div v-if="nodeType === 'M7'" class="m7-form">
        <h3 style="margin-bottom: 20px;">工作联系单编制审批</h3>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系单编号">
              <el-input v-model="form.contact_no" placeholder="系统自动生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="提交日期">
              <el-date-picker v-model="form.submit_date" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="事由">
          <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="请描述联系事项" />
        </el-form-item>

        <el-form-item label="涉及图纸">
          <el-input v-model="form.drawings" placeholder="相关图纸编号" />
        </el-form-item>

        <el-form-item label="支撑材料">
          <el-upload
            action="#"
            :auto-upload="false"
            multiple
            :file-list="attachments"
            @change="handleAttachmentChange"
          >
            <el-button type="default">上传附件</el-button>
          </el-upload>
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="submitForm">提交审批</el-button>
        </el-form-item>
      </div>

      <div v-else-if="nodeType === 'M8'" class="m8-form">
        <h3 style="margin-bottom: 20px;">工程签证执行</h3>
        
        <el-form-item label="签证类型">
          <el-radio-group v-model="form.visa_type">
            <el-radio-button label="technical">技术类</el-radio-button>
            <el-radio-button label="economic">经济类</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="关联工联单">
          <el-select v-model="form.related_contact" placeholder="选择关联的工作联系单">
            <el-option 
              v-for="item in contactList" 
              :key="item.id" 
              :label="item.contact_no + ' - ' + item.reason" 
              :value="item.id" 
            />
          </el-select>
        </el-form-item>

        <el-form-item label="签证金额(元)">
          <el-input-number v-model="form.amount" :precision="2" :min="0" />
        </el-form-item>

        <el-form-item label="现场照片">
          <el-upload
            action="#"
            list-type="picture-card"
            :auto-upload="false"
            multiple
            :file-list="photoFiles"
            @change="handlePhotoChange"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-form-item label="说明">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="submitForm">提交审批</el-button>
        </el-form-item>
      </div>

      <div v-else>
        <el-empty description="该节点表单开发中..." />
      </div>

      <!-- Approval Progress -->
      <el-card v-if="instanceId" style="margin-top: 20px;" shadow="never">
        <template #header>审批进度</template>
        <el-steps :active="currentStep" finish-status="success" align-center>
          <el-step
            v-for="(step, index) in steps"
            :key="step.id"
            :title="getStepTitle(step)"
            :description="getStepDescription(step)"
            :status="getStepStatus(step, index)"
          />
        </el-steps>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { approvalApi, formApi } from '@/api'

const route = useRoute()
const router = useRouter()

const nodeType = computed(() => route.params.nodeType as string)
const instanceId = ref<number | null>(null)
const currentStep = ref(0)
const steps = ref<any[]>([])

const form = ref({
  contact_no: '',
  submit_date: new Date().toISOString().split('T')[0],
  reason: '',
  drawings: '',
  visa_type: 'technical',
  related_contact: null,
  amount: 0,
  description: '',
})

const attachments = ref<any[]>([])
const photoFiles = ref<any[]>([])
const contactList = ref<any[]>([])

async function loadContactList() {
  try {
    const data = await formApi.list({ node_type: 'M7' })
    contactList.value = data || []
  } catch (e) {
    console.error('Failed to load contacts:', e)
  }
}

async function submitForm() {
  try {
    // Create business form first
    const formData = new FormData()
    for (const file of attachments.value) {
      formData.append('files[]', file.raw)
    }
    
    // Then create approval instance
    const instance = await approvalApi.createInstance({
      node_type: nodeType.value,
      initiator_id: getCurrentUserId(),
      project_id: getCurrentProjectId(),
    })
    
    instanceId.value = instance.id
    currentStep.value = 1
    
    ElMessage.success('已提交审批')
  } catch (e: any) {
    ElMessage.error(e.detail || '提交失败')
  }
}

function handleAttachmentChange(file: any) {
  attachments.value.push(file)
}

function handlePhotoChange(file: any) {
  photoFiles.value.push(file)
}

function getStepTitle(step: any): string {
  return `第${step.step_order}步`
}

function getStepDescription(step: any): string {
  return step.department_name || '待处理'
}

function getStepStatus(step: any, index: number): string {
  if (index < currentStep.value) return 'success'
  if (index === currentStep.value) return 'process'
  return 'wait'
}

function getCurrentProjectId(): number {
  return parseInt(localStorage.getItem('currentProjectId') || '0')
}

function getCurrentUserId(): number {
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
  if (nodeType.value === 'M7') {
    loadContactList()
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-form-item {
  margin-bottom: 20px;
}
</style>
