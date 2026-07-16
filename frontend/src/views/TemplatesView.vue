<template>
  <div class="templates-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模板管理</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon> 上传模板
          </el-button>
        </div>
      </template>

      <!-- Template List -->
      <el-table :data="templates" v-loading="loading" style="width: 100%">
        <el-table-column prop="node_type" label="节点" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.node_type }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="模板名称" min-width="200" />
        
        <el-table-column prop="template_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.template_type === 'docx' ? '' : 'success'" size="small">
              {{ row.template_type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="version" label="版本" width="80" />
        
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="!row.is_active" 
              type="success" 
              link 
              @click="activateTemplate(row.id)"
            >
              激活
            </el-button>
            <el-button type="danger" link @click="deleteTemplate(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!templates.length && !loading" description="暂无模板" />
    </el-card>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="上传模板" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="节点">
          <el-select v-model="uploadForm.node_type" placeholder="选择节点">
            <el-option 
              v-for="node in nodeTypes" 
              :key="node" 
              :label="getNodeName(node)" 
              :value="node" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模板类型">
          <el-radio-group v-model="uploadForm.template_type">
            <el-radio-button label="docx">DOCX</el-radio-button>
            <el-radio-button label="xls">XLS</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="模板名称">
          <el-input v-model="uploadForm.name" placeholder="如：工程签证单(C3-1)" />
        </el-form-item>
        
        <el-form-item label="文件">
          <el-upload
            action="#"
            :auto-upload="false"
            :limit="1"
            accept=".docx,.xls,.xlsx"
            @change="handleFileChange"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { templateApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const templates = ref<any[]>([])
const showUploadDialog = ref(false)
const uploading = ref(false)

const uploadForm = ref({
  node_type: '',
  template_type: 'docx',
  name: '',
  file: null as File | null,
})

const nodeTypes = [
  'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10',
  'M11', 'M12', 'M13', 'M24', 'M25',
]

const nodeNames: Record<string, string> = {
  M1: 'M1 基线录入',
  M2: 'M2 任务分解',
  M3: 'M3 策划编制',
  M4: 'M4 策划审核',
  M5: 'M5 回款落实',
  M6: 'M6 认质认价',
  M7: 'M7 联系单',
  M8: 'M8 签证执行',
  M9: 'M9 索赔执行',
  M10: 'M10 设计变更',
  M11: 'M11 月验工计价',
  M12: 'M12 材料结算',
  M13: 'M13 消耗核定',
  M24: 'M24 建造合同',
  M25: 'M25 月度复盘',
}

function getNodeName(nodeType: string): string {
  return nodeNames[nodeType] || nodeType
}

async function loadTemplates() {
  loading.value = true
  try {
    const data = await templateApi.list(undefined, true)
    templates.value = data || []
  } catch (e) {
    console.error('Failed to load templates:', e)
  } finally {
    loading.value = false
  }
}

async function handleFileChange(file: any) {
  uploadForm.value.file = file.raw
}

async function handleUpload() {
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('node_type', uploadForm.value.node_type)
    formData.append('template_type', uploadForm.value.template_type)
    formData.append('name', uploadForm.value.name)
    
    await templateApi.upload(formData)
    ElMessage.success('模板上传成功')
    showUploadDialog.value = false
    uploadForm.value = { node_type: '', template_type: 'docx', name: '', file: null }
    await loadTemplates()
  } catch (e: any) {
    ElMessage.error(e.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function activateTemplate(templateId: number) {
  try {
    await templateApi.activate(templateId)
    ElMessage.success('模板已激活')
    await loadTemplates()
  } catch (e: any) {
    ElMessage.error(e.detail || '操作失败')
  }
}

async function deleteTemplate(templateId: number) {
  try {
    await ElMessageBox.confirm('确定要删除此模板吗？', '警告', { type: 'warning' })
    // TODO: Implement delete API
    ElMessage.success('模板已删除')
    await loadTemplates()
  } catch {}
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
