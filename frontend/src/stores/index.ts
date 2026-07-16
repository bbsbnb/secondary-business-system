import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, projectApi, deptApi } from '@/api'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<any>(null)
  const currentProject = ref<number | null>(localStorage.getItem('currentProjectId') ? parseInt(localStorage.getItem('currentProjectId')!) : null)
  
  const isLoggedIn = computed(() => !!token.value)
  const departmentName = computed(() => userInfo.value?.department_name || '')
  const roleName = computed(() => userInfo.value?.role || '')
  
  async function login(username: string, password: string) {
    try {
      const res = await authApi.login({ username, password })
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      
      userInfo.value = res.user
      localStorage.setItem('user', JSON.stringify(res.user))
      
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      ElMessage.error(error.detail || '登录失败')
      return false
    }
  }
  
  async function fetchMe() {
    try {
      const res = await authApi.getMe()
      userInfo.value = res
      localStorage.setItem('user', JSON.stringify(res))
    } catch (e) {
      logout()
    }
  }
  
  function setCurrentProject(projectId: number) {
    currentProject.value = projectId
    localStorage.setItem('currentProjectId', String(projectId))
  }
  
  function logout() {
    token.value = ''
    userInfo.value = null
    currentProject.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('currentProjectId')
  }
  
  // Init
  if (token.value && !userInfo.value) {
    const saved = localStorage.getItem('user')
    if (saved) {
      try { userInfo.value = JSON.parse(saved) } catch(e) {}
    }
  }
  
  return { token, userInfo, currentProject, isLoggedIn, departmentName, roleName, login, fetchMe, setCurrentProject, logout }
})

export const useProjectStore = defineStore('project', () => {
  const projects = ref<any[]>([])
  const currentProject = ref<any>(null)
  
  async function fetchProjects() {
    try {
      projects.value = await projectApi.list('active')
    } catch (e) {
      projects.value = []
    }
  }
  
  async function selectProject(id: number) {
    try {
      currentProject.value = await projectApi.get(id)
    } catch (e) {
      currentProject.value = null
    }
  }
  
  return { projects, currentProject, fetchProjects, selectProject }
})
