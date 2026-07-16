<template>
  <div class="documents-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>项目资料库</span>
          <el-upload
            :action="uploadUrl"
            :data="uploadData"
            :show-file-list="false"
            accept=".pdf,.docx,.xlsx,.jpg,.png"
            @success="handleUploadSuccess"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon> 上传文档
            </el-button>
          </el-upload>
        </div>
      </template>

      <!-- Filters -->
      <el-form inline style="margin-bottom: 16px;">
        <el-form-item label="分类">
          <el-select v-model="filterCategory" placeholder="全部分类" clearable style="width: 150px;">
            <el-option label="合同" value="contract" />
            <el-option label="招投标文件" value="bidding" />
            <el-option label="签证" value="visa" />
            <el-option label="变更" value="change" />
            <el-option label="照片" value="photo" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源节点">
          <el-select v-model="filterNode" placeholder="全部节点" clearable style="width: 120px;">
            <el-option label="M1" value="M1" />
            <el-option label="M7" value="M7" />
            <el-option label="M8" value="M8" />
            <el-option label="M10" value="M10" />
            <el-option label="M14-M23" value="M14-M23" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-input v-model="searchKeyword" placeholder="搜索文件名" clearable style="width: 200px;" />
        </el-form-item>
      </el-form>

      <!-- Document List -->
      <el-table :data="filteredDocuments" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="文件名" min-width="200">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-icon :size="20">
                <Document v-if="row.file_type === 'pdf'" />
                <EditPen v-else-if="['docx','doc'].includes(row.file_type)" />
                <Grid v-else-if="['xlsx','xls'].includes(row.file_type)" />
                <Picture v-else-if="['jpg','jpeg','png'].includes(row.file_type)" />
                <FolderOpened v-else />
              </el-icon>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getCategoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            {{ row.file_type.toUpperCase() }}
          </template>
        </el-table-column>
        
        <el-table-column prop="related_node" label="来源节点" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.related_node" size="small" effect="plain">{{ row.related_node }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="auto_categorized" label="自动归档" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.auto_categorized" type="success" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="previewDocument(row)">预览</el-button>
            <el-button type="danger" link @click="deleteDocument(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!filteredDocuments.length && !loading" description="暂无文档" />
    </el-card>

    <!-- Preview Dialog -->
    <el-dialog v-model="previewVisible" :title="previewDoc?.title" width="80%">
      <div v-if="previewDoc" class="preview-container">
        <iframe 
          v-if="isPreviewable(previewDoc.file_type)"
          :src="getFileUrl(previewDoc.file_path)"
          style="width: 100%; height: 600px; border: none;"
        />
        <div v-else class="file-info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="文件名">{{ previewDoc.title }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ previewDoc.file_type.toUpperCase() }}</el-descriptions-item>
            <el-descriptions-item label="大小">{{ formatFileSize(previewDoc.file_size) }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ getCategoryLabel(previewDoc.category) }}</el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 20px; text-align: center;">
            <el-button type="primary" @click="downloadFile(previewDoc.file_path)">
              <el-icon><Download /></el-icon> 下载文件
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import { documentApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const documents = ref<any[]>([])
const searchKeyword = ref('')
const filterCategory = ref('')
const filterNode = ref('')

const previewVisible = ref(false)
const previewDoc = ref<any>(null)

const filteredDocuments = computed(() => {
  let result = documents.value
  
  if (filterCategory.value) {
    result = result.filter(d => d.category === filterCategory.value)
  }
  
  if (filterNode.value) {
    result = result.filter(d => d.related_node === filterNode.value)
  }
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(d => d.title.toLowerCase().includes(keyword))
  }
  
  return result
})

async function loadDocuments() {
  loading.value = true
  try {
    const projectId = getCurrentProjectId()
    const data = await documentApi.list({ project_id: projectId })
    documents.value = data || []
  } catch (e) {
    console.error('Failed to load documents:', e)
  } finally {
    loading.value = false
  }
}

async function handleUploadSuccess(response: any) {
  ElMessage.success('上传成功')
  await loadDocuments()
}

function previewDocument(doc: any) {
  previewDoc.value = doc
  previewVisible.value = true
}

async function deleteDocument(docId: number) {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '警告', { type: 'warning' })
    await documentApi.delete(docId)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch {}
}

function isPreviewable(fileType: string): boolean {
  return ['pdf', 'jpg', 'jpeg', 'png'].includes(fileType.toLowerCase())
}

function getFileUrl(filePath: string): string {
  // In production, this would be a signed URL or proxy endpoint
  return `/uploads/${filePath}`
}

function downloadFile(filePath: string) {
  const link = document.createElement('a')
  link.href = `/uploads/${filePath}`
  link.download = filePath.split('/').pop() || 'file'
  link.click()
}

function getCategoryLabel(category: string): string {
  const map: Record<string, string> = {
    contract: '合同',
    bidding: '招投标文件',
    visa: '签证',
    change: '变更',
    photo: '照片',
    other: '其他',
  }
  return map[category] || category
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

function getCurrentProjectId(): number {
  return parseInt(localStorage.getItem('currentProjectId') || '0')
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-container {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-info {
  text-align: center;
}
</style>
