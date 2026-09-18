<template>
  <div class="page">
    <div class="page-header">
      <h2>数据概览</h2>
      <p class="subtitle">青岛大气 PM2.5 / PM10 小时级监测数据 · {{ stats.startDate }} 至 {{ stats.endDate }}</p>
    </div>

    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">PM2.5 均值</div>
        <div class="kpi-value">{{ stats.pm25Avg }}<span class="unit">μg/m³</span></div>
        <div class="kpi-foot">中位数 {{ stats.pm25Median }} · 峰值 {{ stats.pm25Max }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">PM10 均值</div>
        <div class="kpi-value">{{ stats.pm10Avg }}<span class="unit">μg/m³</span></div>
        <div class="kpi-foot">最低 {{ stats.pm10Min }} · 峰值 {{ stats.pm10Max }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">样本总量</div>
        <div class="kpi-value">{{ formatNum(stats.total) }}<span class="unit">条</span></div>
        <div class="kpi-foot">小时级监测记录</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">PM2.5/PM10 相关性</div>
        <div class="kpi-value">{{ stats.pearson }}</div>
        <div class="kpi-foot">皮尔逊相关系数（高度正相关）</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">日均浓度变化趋势（{{ daily.length }} 天）</div>
      <div ref="trendChart" class="chart"></div>
    </div>

    <div class="card-row">
      <div class="card flex-1">
        <div class="card-title">空气质量等级分布（按日均值）</div>
        <div ref="pieChart" class="chart-sm"></div>
      </div>
      <div class="card flex-1">
        <div class="card-title">24 小时浓度日变化</div>
        <div ref="hourChart" class="chart-sm"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import { loadData, summaryStats, dailyAverages, gradeDistribution, hourlyStats } from '../utils/data'

const trendChart = ref(null)
const pieChart = ref(null)
const hourChart = ref(null)
const stats = ref({
  total: 0, startDate: '', endDate: '',
  pm25Avg: 0, pm10Avg: 0, pm25Max: 0, pm10Max: 0,
  pm25Min: 0, pm10Min: 0, pm25Median: 0, ratioAvg: 0, pearson: 0
})
const daily = ref([])

const formatNum = (n) => n.toLocaleString()

onMounted(async () => {
  const data = await loadData()
  stats.value = summaryStats(data)
  daily.value = dailyAverages(data)
  const grades = gradeDistribution(daily.value)
  const hourly = hourlyStats(data)

  const baseText = { color: '#606266' }

  // 趋势图
  echarts.init(trendChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0, textStyle: baseText },
    grid: { left: 50, right: 30, top: 40, bottom: 60 },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', height: 20, bottom: 10 }
    ],
    xAxis: {
      type: 'category',
      data: daily.value.map((d) => d.date),
      axisLabel: { color: '#909399', rotate: 0 }
    },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel: { color: '#909399' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    series: [
      {
        name: 'PM2.5',
        type: 'line',
        data: daily.value.map((d) => d.pm25),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.2, color: '#ee6666' },
        areaStyle: { color: 'rgba(238,102,102,0.08)' }
      },
      {
        name: 'PM10',
        type: 'line',
        data: daily.value.map((d) => d.pm10),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.2, color: '#5470c6' }
      }
    ]
  })

  // 饼图
  const pieColors = {
    优: '#00e400',
    良: '#c9c900',
    轻度污染: '#ff7e00',
    中度污染: '#ff0000',
    重度污染: '#99004c',
    严重污染: '#7e0023'
  }
  echarts.init(pieChart.value).setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 天 ({d}%)' },
    legend: { bottom: 0, textStyle: baseText },
    series: [
      {
        type: 'pie',
        radius: ['40%', '68%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        label: { formatter: '{b}\n{d}%', fontSize: 11 },
        data: grades.map((g) => ({ name: g.name, value: g.value, itemStyle: { color: pieColors[g.name] } }))
      }
    ]
  })

  // 24小时图
  echarts.init(hourChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0, textStyle: baseText },
    grid: { left: 45, right: 20, top: 35, bottom: 30 },
    xAxis: {
      type: 'category',
      data: hourly.map((h) => h.hour + '时'),
      axisLabel: { color: '#909399', interval: 1 }
    },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel: { color: '#909399' }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    series: [
      { name: 'PM2.5', type: 'line', smooth: true, data: hourly.map((h) => h.pm25), itemStyle: { color: '#ee6666' } },
      { name: 'PM10', type: 'line', smooth: true, data: hourly.map((h) => h.pm10), itemStyle: { color: '#5470c6' } }
    ]
  })

  window.addEventListener('resize', () => {
    ;[trendChart, pieChart, hourChart].forEach((r) => echarts.getInstanceByDom(r.value)?.resize())
  })
})
</script>

<style scoped>
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: #1a3a5c;
}
.subtitle {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.kpi-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #2b7cff;
}
.kpi-card:nth-child(2) {
  border-left-color: #ee6666;
}
.kpi-card:nth-child(3) {
  border-left-color: #91cc75;
}
.kpi-label {
  font-size: 13px;
  color: #909399;
}
.kpi-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 6px 0;
}
.unit {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
  margin-left: 4px;
}
.kpi-foot {
  font-size: 12px;
  color: #c0c4cc;
}

.card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}
.card-row {
  display: flex;
  gap: 16px;
}
.flex-1 {
  flex: 1;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}
.chart {
  width: 100%;
  height: 380px;
}
.chart-sm {
  width: 100%;
  height: 320px;
}
</style>
