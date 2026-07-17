import api from './http'

// ========== 认证 ==========
export const authApi = {
  login: (data: { username: string; password: string }) => 
    api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  refresh: (refreshToken: string) => 
    api.post('/auth/refresh', { refresh_token: refreshToken }),
}

// ========== 项目 ==========
export const projectApi = {
  list: (params?: any) => api.get('/projects', { params }),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: any) => api.post('/projects', data),
  update: (id: number, data: any) => api.put(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
  getMembers: (id: number) => api.get(`/projects/${id}/members`),
  addMember: (id: number, data: any) => api.post(`/projects/${id}/members`, data),
}

// ========== 部门 ==========
export const deptApi = {
  list: () => api.get('/departments'),
  get: (id: number) => api.get(`/departments/${id}`),
  create: (data: any) => api.post('/departments', data),
  update: (id: number, data: any) => api.put(`/departments/${id}`, data),
  delete: (id: number) => api.delete(`/departments/${id}`),
}

// ========== 权限矩阵 ==========
export const permissionApi = {
  getMatrix: () => api.get('/permissions/matrix'),
  getDeptRoles: () => api.get('/permissions/departments-roles'),
  getNodePermissions: (nodeType: string) => 
    api.get(`/permissions/nodes/${nodeType}/permissions`),
}

// ========== 基线数据(M1) ==========
export const baselineApi = {
  get: (projectId: number) => api.get(`/baseline/${projectId}`),
  create: (projectId: number, data: any) => api.post(`/baseline/${projectId}`, data),
  update: (id: number, data: any) => api.put(`/baseline/${id}`, data),
  lock: (id: number, data?: any) => api.post(`/baseline/${id}/lock`, data || { confirmed: true }),
  unlock: (id: number, data: any) => api.post(`/baseline/${id}/unlock`, data),
}

// ========== 业务表单 ==========
export const formApi = {
  list: (params?: any) => api.get('/forms', { params }),
  get: (id: number) => api.get(`/forms/${id}`),
  create: (data: any) => api.post('/forms', data),
  update: (id: number, data: any) => api.put(`/forms/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/forms/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== 审批引擎 ==========
export const approvalApi = {
  createInstance: (data: any) => api.post('/approval/instances', data),
  getMyPending: () => api.get('/approval/my-pending'),
  getMyHistory: (limit?: number) => api.get('/approval/my-history', { params: { limit } }),
  getInstance: (id: number) => api.get(`/approval/${id}`),
  approve: (id: number, data: { opinion?: string }) => 
    api.post(`/approval/${id}/approve`, data),
  reject: (id: number, data: { opinion: string }) => 
    api.post(`/approval/${id}/reject`, data),
  getNodeTemplate: (nodeType: string) => api.get(`/approval/templates/${nodeType}`),
  initDefaultTemplates: () => api.post('/approval/templates/init-defaults'),
}

// ========== M6 认质认价 ==========
export const m6Api = {
  list: (params?: any) => api.get('/m6/price/list', { params }),
  get: (id: number) => api.get(`/m6/price/${id}`),
  create: (data: any) => api.post('/m6/price', data),
  update: (id: number, data: any) => api.put(`/m6/price/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m6/price/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M7 工作联系单 ==========
export const m7Api = {
  list: (params?: any) => api.get('/m7/contact/list', { params }),
  get: (id: number) => api.get(`/m7/contact/${id}`),
  create: (data: any) => api.post('/m7/contact', data),
  update: (id: number, data: any) => api.put(`/m7/contact/${id}`, data),
  submit: (id: number) => api.post(`/m7/contact/${id}/submit`),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m7/contact/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M8 签证执行 ==========
export const m8Api = {
  list: (params?: any) => api.get('/m8/visa/list', { params }),
  get: (id: number) => api.get(`/m8/visa/${id}`),
  create: (data: any) => api.post('/m8/visa', data),
  update: (id: number, data: any) => api.put(`/m8/visa/${id}`, data),
  submit: (id: number) => api.post(`/m8/visa/${id}/submit`),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m8/visa/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M9 索赔执行 ==========
export const m9Api = {
  list: (params?: any) => api.get('/m9/claim/list', { params }),
  get: (id: number) => api.get(`/m9/claim/${id}`),
  create: (data: any) => api.post('/m9/claim', data),
  update: (id: number, data: any) => api.put(`/m9/claim/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m9/claim/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M10 设计变更 ==========
export const m10Api = {
  list: (params?: any) => api.get('/m10/change/list', { params }),
  get: (id: number) => api.get(`/m10/change/${id}`),
  create: (data: any) => api.post('/m10/change', data),
  update: (id: number, data: any) => api.put(`/m10/change/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m10/change/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M11 月验工计价 ==========
export const m11Api = {
  list: (params?: any) => api.get('/m11/verification/list', { params }),
  get: (id: number) => api.get(`/m11/verification/${id}`),
  create: (data: any) => api.post('/m11/verification', data),
  update: (id: number, data: any) => api.put(`/m11/verification/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m11/verification/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M12 材料结算 ==========
export const m12Api = {
  list: (params?: any) => api.get('/m12/material/list', { params }),
  get: (id: number) => api.get(`/m12/material/${id}`),
  create: (data: any) => api.post('/m12/material', data),
  update: (id: number, data: any) => api.put(`/m12/material/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m12/material/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== M13 消耗核定 ==========
export const m13Api = {
  list: (params?: any) => api.get('/m13/consumption/list', { params }),
  get: (id: number) => api.get(`/m13/consumption/${id}`),
  create: (data: any) => api.post('/m13/consumption', data),
  update: (id: number, data: any) => api.put(`/m13/consumption/${id}`, data),
  uploadAttachment: (id: number, formData: FormData) => 
    api.post(`/m13/consumption/${id}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}

// ========== 建造合同(M24) ==========
export const contractApi = {
  get: (projectId: number, month: string) => 
    api.get(`/contracts/${projectId}/${month}`),
  createOrUpdate: (projectId: number, month: string) => api.post(`/contracts/${projectId}/${month}`),
  update: (projectId: number, month: string, data: any) => api.put(`/contracts/${projectId}/${month}`, data),
}

// ========== 模板管理 ==========
export const templateApi = {
  list: (projectId?: number, activeOnly?: boolean) => 
    api.get('/templates', { params: { project_id: projectId, active_only: activeOnly } }),
  upload: (formData: FormData) => 
    api.post('/templates/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  activate: (id: number) => api.post(`/templates/${id}/activate`),
  download: (id: number) => api.get(`/templates/${id}/download`),
}

// ========== 资料库 ==========
export const documentApi = {
  list: (params?: any) => api.get('/documents', { params }),
  get: (id: number) => api.get(`/documents/${id}`),
  create: (data: any) => api.post('/documents', data),
  upload: (formData: FormData) => 
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  delete: (id: number) => api.delete(`/documents/${id}`),
}

// ========== 预警中心 ==========
export const alertApi = {
  list: (params?: any) => api.get('/alerts/list', { params }),
  stats: (params?: any) => api.get('/alerts/stats', { params }),
  get: (id: number) => api.get(`/alerts/${id}`),
  resolve: (id: number) => api.post(`/alerts/${id}/resolve`),
  markAllRead: () => api.post('/alerts/mark-all-read'),
  createManual: (data: any) => api.post('/alerts/create-manual', data),
}

// ========== 驾驶舱 ==========
export const dashboardApi = {
  getSummary: (params?: any) => api.get('/dashboard/dashboard', { params }),
  getMonthlyTrend: (params?: any) => api.get('/dashboard/monthly-trend', { params }),
}

// ========== 移动端 ==========
export const mobileApi = {
  quickStats: (projectId?: number) => 
    api.get('/mobile/quick-stats', { params: { project_id: projectId } }),
  getPending: (page?: number, pageSize?: number) => 
    api.get('/mobile/approvals', { params: { page, page_size: pageSize } }),
  approveAction: (instanceId: number, action: string, opinion?: string) => 
    api.post(`/mobile/approval/${instanceId}/action`, { action, opinion }),
}
