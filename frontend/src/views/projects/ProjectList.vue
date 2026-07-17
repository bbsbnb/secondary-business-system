<template>
  <div class="project-list">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <span class="card-title">项目管理</span>
            <p>维护项目基础信息，并选择当前项目用于月度节点填报</p>
          </div>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </div>
      </template>

      <div class="toolbar">
        <el-input
          v-model="keyword"
          clearable
          placeholder="搜索项目编号、名称或合同编号"
          style="width: 280px"
        />
        <el-select v-model="statusFilter" style="width: 140px" @change="loadProjects">
          <el-option label="进行中" value="active" />
          <el-option label="已归档" value="archived" />
        </el-select>
        <el-button @click="loadProjects">刷新</el-button>
      </div>

      <el-table :data="filteredProjects" v-loading="loading" style="width: 100%">
        <el-table-column prop="project_code" label="项目编号" width="150" />
        <el-table-column prop="project_name" label="项目名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="contract_no" label="合同编号" width="160" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="selectProject(row)">设为当前</el-button>
            <el-button type="success" link @click="openBaseline(row)">基线</el-button>
            <el-button
              type="danger"
              link
              :disabled="row.status !== 'active'"
              @click="archiveProject(row)"
            >
              归档
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!filteredProjects.length && !loading" description="暂无项目" />
    </el-card>

    <el-dialog v-model="showCreateDialog" title="新建项目" width="520px">
      <el-form ref="formRef" :model="createForm" :rules="rules" label-width="96px">
        <el-form-item label="项目编号" prop="project_code">
          <el-input v-model="createForm.project_code" placeholder="如：PRJ-2026-001" />
        </el-form-item>
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="createForm.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="合同编号">
          <el-input v-model="createForm.contract_no" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { projectApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const projects = ref<any[]>([])
const showCreateDialog = ref(false)
const keyword = ref('')
const statusFilter = ref('active')
const formRef = ref<FormInstance>()

const createForm = ref({
  project_code: '',
  project_name: '',
  contract_no: '',
})

const rules: FormRules = {
  project_code: [{ required: true, message: '请输入项目编号', trigger: 'blur' }],
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

const filteredProjects = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return projects.value
  return projects.value.filter((project) => {
    return [project.project_code, project.project_name, project.contract_no]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(text))
  })
})

async function loadProjects() {
  loading.value = true
  try {
    const data = await projectApi.list({ status_filter: statusFilter.value })
    projects.value = data || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '项目加载失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createForm.value = { project_code: '', project_name: '', contract_no: '' }
  showCreateDialog.value = true
}

async function handleCreate() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    const project = await projectApi.create(createForm.value)
    localStorage.setItem('currentProjectId', String(project.id))
    ElMessage.success('项目创建成功，已设为当前项目')
    showCreateDialog.value = false
    await loadProjects()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || error.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

function selectProject(project: any) {
  localStorage.setItem('currentProjectId', String(project.id))
  ElMessage.success(`当前项目已切换为：${project.project_name}`)
}

function openBaseline(project: any) {
  localStorage.setItem('currentProjectId', String(project.id))
  router.push('/monthly/M1')
}

async function archiveProject(project: any) {
  try {
    await ElMessageBox.confirm(`确定归档项目“${project.project_name}”吗？`, '归档项目', {
      type: 'warning',
    })
    await projectApi.delete(project.id)
    if (localStorage.getItem('currentProjectId') === String(project.id)) {
      localStorage.removeItem('currentProjectId')
    }
    ElMessage.success('项目已归档')
    await loadProjects()
  } catch {}
}

function formatDate(dateStr: string): string {
  return dateStr ? dayjs(dateStr).format('YYYY-MM-DD HH:mm') : '-'
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.project-list {
  padding: 20px;
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
</style>
