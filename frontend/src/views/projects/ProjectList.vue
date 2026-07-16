<template>
  <div class="project-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>项目管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 新建项目
          </el-button>
        </div>
      </template>

      <el-table :data="projects" v-loading="loading" style="width: 100%">
        <el-table-column prop="project_code" label="项目编号" width="150" />
        <el-table-column prop="project_name" label="项目名称" min-width="200" />
        <el-table-column prop="contract_no" label="合同编号" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="selectProject(row)">进入</el-button>
            <el-button type="danger" link @click="deleteProject(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!projects.length && !loading" description="暂无项目" />
    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建项目" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="项目编号" required>
          <el-input v-model="createForm.project_code" placeholder="如：PRJ-2026-001" />
        </el-form-item>
        <el-form-item label="项目名称" required>
          <el-input v-model="createForm.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="合同编号">
          <el-input v-model="createForm.contract_no" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import { projectApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const projects = ref<any[]>([])
const showCreateDialog = ref(false)
const creating = ref(false)

const createForm = ref({
  project_code: '',
  project_name: '',
  contract_no: '',
})

async function loadProjects() {
  loading.value = true
  try {
    const data = await projectApi.list('active')
    projects.value = data || []
  } catch (e) {
    console.error('Failed to load projects:', e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.value.project_code || !createForm.value.project_name) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  creating.value = true
  try {
    await projectApi.create(createForm.value)
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    createForm.value = { project_code: '', project_name: '', contract_no: '' }
    await loadProjects()
  } catch (e: any) {
    ElMessage.error(e.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function selectProject(project: any) {
  // TODO: Set current project in store
  window.location.href = `/projects/${project.id}`
}

async function deleteProject(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除此项目吗？', '警告', {
      type: 'warning',
    })
    // TODO: Implement delete API
    ElMessage.success('项目已删除')
    await loadProjects()
  } catch {}
}

function formatDate(dateStr: string): string {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
