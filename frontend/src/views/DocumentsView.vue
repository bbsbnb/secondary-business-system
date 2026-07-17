<template>
  <div class="documents-view">
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
            <span class="card-title">项目资料库</span>
            <p>统一管理合同、签证、变更、照片和节点支撑资料</p>
          </div>
          <div class="header-actions">
            <el-button @click="resetFilters">重置</el-button>
            <el-button @click="loadDocuments">刷新</el-button>
            <el-button type="primary" @click="openUploadDialog">
              <el-icon><Upload /></el-icon>
              上传文档
            </el-button>
          </div>
        </div>
      </template>

      <div class="toolbar">
        <el-select v-model="filters.category" clearable placeholder="全部分类" style="width: 150px" @change="loadDocuments">
          <el-option v-for="item in categoryOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.related_node" clearable placeholder="全部节点" style="width: 140px" @change="loadDocuments">
          <el-option v-for="node in nodeOptions" :key="node" :label="node" :value="node" />
        </el-select>
        <el-input v-model="keyword" clearable placeholder="搜索文件名" style="width: 240px" />
      </div>

      <el-table :data="filteredDocuments" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="文件名" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="file-cell">
              <el-icon :size="20"><component :is="getFileIcon(row.file_type)" /></el-icon>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }"><el-tag size="small">{{ getCategoryLabel(row.category) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="90" align="center">
          <template #default="{ row }">{{ (row.file_type || '-').toUpperCase() }}</template>
        </el-table-column>
        <el-table-column prop="related_node" label="来源节点" width="110" align="center">
          <template #default="{ row }"><el-tag v-if="row.related_node" effect="plain" size="small">{{ row.related_node }}</el-tag><span v-else>-</span></template>
        </el-table-column>
        <el-table-column label="大小" width="100" align="right">
          <template #default="{ row }">{{ formatFileSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="previewDocument(row)">查看</el-button>
            <el-button type="danger" link @click="deleteDocument(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!filteredDocuments.length && !loading" description="暂无文档" />
    </el-card>

    <el-dialog v-model="uploadVisible" title="上传文档" width="560px">
      <el-form :model="uploadForm" label-width="96px">
        <el-form-item label="文件" required>
          <el-upload
            action="#"
            :auto-upload="false"
            :limit="1"
            :file-list="uploadFiles"
            @change="handleFileChange"
            @remove="handleFileRemove"
          >
            <el-button>选择文件</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="标题" required>
          <el-input v-model="uploadForm.title" placeholder="默认使用文件名" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="uploadForm.category" style="width: 100%">
            <el-option v-for="item in categoryOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源节点">
          <el-select v-model="uploadForm.related_node" clearable style="width: 100%">
            <el-option v-for="node in nodeOptions" :key="node" :label="node" :value="node" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible" :title="previewDoc?.title" width="640px">
      <el-descriptions v-if="previewDoc" :column="2" border>
        <el-descriptions-item label="文件名">{{ previewDoc.title }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ previewDoc.file_type?.toUpperCase() }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ getCategoryLabel(previewDoc.category) }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatFileSize(previewDoc.file_size) }}</el-descriptions-item>
        <el-descriptions-item label="来源节点">{{ previewDoc.related_node || '-' }}</el-descriptions-item>
        <el-descriptions-item label="上传时间">{{ formatDate(previewDoc.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { Document, EditPen, FolderOpened, Grid, Picture, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { documentApi } from '@/api'

const loading = ref(false)
const uploading = ref(false)
const documents = ref<any[]>([])
const keyword = ref('')
const uploadVisible = ref(false)
const previewVisible = ref(false)
const previewDoc = ref<any>(null)
const uploadFiles = ref<any[]>([])

const filters = ref({ category: '', related_node: '' })
const uploadForm = ref({ title: '', category: 'document', related_node: '' })

const categoryOptions = [
  { label: '合同', value: 'contract' },
  { label: '招投标', value: 'bidding' },
  { label: '签证', value: 'visa' },
  { label: '变更', value: 'change' },
  { label: '照片', value: 'photo' },
  { label: '资料', value: 'document' },
  { label: '其他', value: 'other' },
]
const nodeOptions = ['M1', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12', 'M13', 'M24', 'M25']

const filteredDocuments = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return documents.value
  return documents.value.filter((doc) => String(doc.title || '').toLowerCase().includes(text))
})

const statCards = computed(() => {
  const totalSize = documents.value.reduce((sum, doc) => sum + Number(doc.file_size || 0), 0)
  const autoCount = documents.value.filter((doc) => doc.auto_categorized).length
  return [
    { label: '文档总数', value: documents.value.length, note: '当前筛选范围', color: '#409EFF' },
    { label: '节点资料', value: documents.value.filter((doc) => doc.related_node).length, note: '已关联流程节点', color: '#67C23A' },
    { label: '自动归档', value: autoCount, note: '系统归类资料', color: '#E6A23C' },
    { label: '占用空间', value: formatFileSize(totalSize), note: '文件大小合计', color: '#909399' },
  ]
})

async function loadDocuments() {
  loading.value = true
  try {
    const params: Record<string, any> = { project_id: getCurrentProjectId() || 1 }
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.related_node) params.related_node = filters.value.related_node
    documents.value = await documentApi.list(params) || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '文档加载失败')
  } finally {
    loading.value = false
  }
}

function openUploadDialog() {
  uploadFiles.value = []
  uploadForm.value = { title: '', category: 'document', related_node: '' }
  uploadVisible.value = true
}

function handleFileChange(file: any) {
  uploadFiles.value = [file]
  if (!uploadForm.value.title) uploadForm.value.title = file.name
}

function handleFileRemove() {
  uploadFiles.value = []
}

async function submitUpload() {
  const file = uploadFiles.value[0]?.raw
  if (!file) {
    ElMessage.warning('请选择文件')
    return
  }
  if (!uploadForm.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', uploadForm.value.title)
    formData.append('category', uploadForm.value.category)
    formData.append('project_id', String(getCurrentProjectId() || 1))
    formData.append('auto_categorized', 'false')
    if (uploadForm.value.related_node) formData.append('related_node', uploadForm.value.related_node)
    await documentApi.upload(formData)
    ElMessage.success('上传成功')
    uploadVisible.value = false
    await loadDocuments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

function previewDocument(doc: any) {
  previewDoc.value = doc
  previewVisible.value = true
}

async function deleteDocument(doc: any) {
  try {
    await ElMessageBox.confirm(`确定删除“${doc.title}”吗？`, '删除文档', { type: 'warning' })
    await documentApi.delete(doc.id)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch {}
}

function resetFilters() {
  filters.value = { category: '', related_node: '' }
  keyword.value = ''
  loadDocuments()
}

function getFileIcon(fileType: string) {
  const type = String(fileType || '').toLowerCase()
  if (type === 'pdf') return Document
  if (['doc', 'docx'].includes(type)) return EditPen
  if (['xls', 'xlsx'].includes(type)) return Grid
  if (['jpg', 'jpeg', 'png'].includes(type)) return Picture
  return FolderOpened
}

function getCategoryLabel(category: string): string {
  return categoryOptions.find((item) => item.value === category)?.label || category || '-'
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(dateStr: string): string {
  return dateStr ? dayjs(dateStr).format('YYYY-MM-DD HH:mm') : '-'
}

function getCurrentProjectId(): number {
  return Number(localStorage.getItem('currentProjectId') || '1')
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.documents-view {
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
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.card-header,
.header-actions,
.toolbar,
.file-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-header {
  justify-content: space-between;
  align-items: flex-start;
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

.toolbar {
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
