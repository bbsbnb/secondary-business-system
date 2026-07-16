<template>
  <el-container class="main-layout">
    <!-- Sidebar -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <el-icon :size="28"><OfficeBuilding /></el-icon>
        <span v-show="!isCollapse" class="logo-text">天行建筑</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>驾驶舱</template>
        </el-menu-item>
        
        <el-sub-menu index="approval">
          <template #title>
            <el-icon><Tickets /></el-icon>
            <span>审批中心</span>
          </template>
          <el-menu-item index="/approval/pending">我的待办</el-menu-item>
          <el-menu-item index="/approval/history">我的已办</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="monthly">
          <template #title>
            <el-icon><Calendar /></el-icon>
            <span>月度节点</span>
          </template>
          <el-menu-item index="/monthly/M1">M1 基线录入</el-menu-item>
          <el-menu-item index="/monthly/M2">M2 任务分解</el-menu-item>
          <el-menu-item index="/monthly/M3">M3 策划编制</el-menu-item>
          <el-menu-item index="/monthly/M4">M4 策划审核</el-menu-item>
          <el-menu-item index="/monthly/M5">M5 回款落实</el-menu-item>
          <el-menu-item index="/monthly/M6">M6 认质认价</el-menu-item>
          <el-menu-item index="/monthly/M7">M7 联系单</el-menu-item>
          <el-menu-item index="/monthly/M8">M8 签证执行</el-menu-item>
          <el-menu-item index="/monthly/M9">M9 索赔执行</el-menu-item>
          <el-menu-item index="/monthly/M10">M10 设计变更</el-menu-item>
          <el-menu-item index="/monthly/M11">M11 月验工计价</el-menu-item>
          <el-menu-item index="/monthly/M12">M12 材料结算</el-menu-item>
          <el-menu-item index="/monthly/M13">M13 消耗核定</el-menu-item>
          <el-menu-item index="/monthly/M24">M24 建造合同</el-menu-item>
          <el-menu-item index="/monthly/M25">M25 月度复盘</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/projects">
          <el-icon><Files /></el-icon>
          <template #title>项目管理</template>
        </el-menu-item>
        
        <el-sub-menu index="dashboards">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>数据看板</span>
          </template>
          <el-menu-item index="/dashboards/cost">成本看板</el-menu-item>
          <el-menu-item index="/dashboards/schedule">进度看板</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/documents">
          <el-icon><FolderOpened /></el-icon>
          <template #title>项目资料库</template>
        </el-menu-item>
        
        <el-menu-item index="/alerts">
          <el-icon><Warning /></el-icon>
          <template #title>预警中心</template>
        </el-menu-item>
        
        <el-menu-item index="/contracts">
          <el-icon><DocumentChecked /></el-icon>
          <template #title>建造合同(M24)</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- Main content -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentBreadcrumb }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-avatar :size="28">{{ userName?.charAt(0) || 'U' }}</el-avatar>
              <span class="username">{{ userName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)
const userName = computed(() => userStore.userInfo?.real_name || '')
const currentBreadcrumb = computed(() => {
  const meta = route.matched.find(r => r.meta?.title)
  return meta?.title || ''
})

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #3a4a5e;
}

.el-menu {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  font-size: 20px;
  color: #606266;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  font-size: 14px;
  color: #303133;
}

.content {
  background: #f0f2f5;
  min-height: calc(100vh - 60px);
  padding: 20px;
}
</style>
