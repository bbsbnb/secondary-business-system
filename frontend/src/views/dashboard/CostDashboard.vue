<template>
  <div class="cost-dashboard">
    <el-card>
      <template #header>
        <span>成本看板</span>
      </template>

      <!-- KPI Cards -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-statistic title="原合同价" :value="contract?.original_contract_amount || 0" :precision="2" prefix="¥" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="预计总收入" :value="contract?.total_revenue || 0" :precision="2" prefix="¥" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="总成本" :value="contract?.total_cost || 0" :precision="2" prefix="¥" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="利润率" :value="contract?.profit_ratio || 0" :precision="2" suffix="%" :value-style="{ color: (contract?.profit_ratio || 0) >= 8 ? '#67C23A' : '#F56C6C' }" />
        </el-col>
      </el-row>

      <!-- Cost Breakdown Chart -->
      <div ref="costChartRef" style="height: 400px; margin-bottom: 20px;"></div>

      <!-- Historical Trend -->
      <h4 style="margin-bottom: 10px;">历史成本趋势</h4>
      <div ref="trendChartRef" style="height: 300px;"></div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { contractApi } from '@/api'

const contract = ref<any>(null)
const costChartRef = ref<HTMLDivElement>()
const trendChartRef = ref<HTMLDivElement>()

async function loadContract() {
  try {
    const projectId = getCurrentProjectId()
    const month = dayjs().format('YYYY-MM')
    const data = await contractApi.get(projectId, month)
    contract.value = data
  } catch (e) {
    console.error('Failed to load contract:', e)
  }
}

function initCostChart() {
  if (!costChartRef.value) return
  const chart = echarts.init(costChartRef.value)
  
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['收入', '成本', '利润'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: ['签证', '索赔', '变更', '验工', '消耗', '材料结算'] },
    yAxis: { type: 'value' },
    series: [
      { name: '收入', type: 'bar', stack: 'total', data: [contract.value?.visa_amount || 0, contract.value?.claim_amount || 0, contract.value?.change_amount || 0] },
      { name: '成本', type: 'bar', stack: 'total', data: [contract.value?.verified_amount || 0, 0, contract.value?.consumption_amount || 0, contract.value?.material_settlement || 0] },
    ],
  })
}

function initTrendChart() {
  if (!trendChartRef.value) return
  const chart = echarts.init(trendChartRef.value)
  
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['计划成本', '实际成本'] },
    xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
    yAxis: { type: 'value' },
    series: [
      { name: '计划成本', type: 'line', data: [100, 120, 150, 180, 200, 220], smooth: true },
      { name: '实际成本', type: 'line', data: [95, 115, 155, 175, 210, 225], smooth: true },
    ],
  })
}

function getCurrentProjectId(): number {
  return parseInt(localStorage.getItem('currentProjectId') || '0')
}

onMounted(() => {
  loadContract()
  setTimeout(() => {
    initCostChart()
    initTrendChart()
  }, 100)
})
</script>

<style scoped>
.cost-dashboard {
  padding: 0;
}
</style>
