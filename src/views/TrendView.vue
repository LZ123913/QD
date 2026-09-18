<template>
  <div class="page">
    <div class="page-header">
      <h2>趋势分析</h2>
      <p class="subtitle">从日、周、月、季节多个时间维度揭示污染物浓度变化规律</p>
    </div>

    <div class="card">
      <div class="card-title">
        <span class="dot"></span>24 小时日变化规律
      </div>
      <div ref="hourChart" class="chart"></div>
      <div class="insight">
        <b>📌 分析：</b>曲线呈现典型的"双峰"特征，早晚高峰（约 8-9 时、19-22 时）浓度上升，与通勤交通排放高度吻合；
        正午前后（12-15 时）浓度最低，得益于大气扩散条件最佳。
      </div>
    </div>

    <div class="card-row">
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>周变化规律（工作日 vs 周末）</div>
        <div ref="weekChart" class="chart-md"></div>
      </div>
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>季节浓度对比</div>
        <div ref="seasonChart" class="chart-md"></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span class="dot"></span>月度变化规律</div>
      <div ref="monthChart" class="chart"></div>
      <div class="insight">
        <b>📌 分析：</b>冬季（11 月-次年 2 月）浓度显著偏高，与北方供暖排放及冬季静稳天气不利于污染物扩散有关；
        夏季（6-8 月）浓度最低，受青岛沿海海风扩散及降水冲刷作用明显，体现了北方沿海城市的季节性特征。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import { loadData, hourlyStats, weeklyStats, monthlyStats, seasonalStats } from '../utils/data'

const hourChart = ref(null)
const weekChart = ref(null)
const monthChart = ref(null)
const seasonChart = ref(null)

const axisLabel = { color: '#909399' }
const splitLine = { lineStyle: { color: '#f0f0f0' } }

onMounted(async () => {
  const data = await loadData()
  const hourly = hourlyStats(data)
  const weekly = weeklyStats(data)
  const monthly = monthlyStats(data)
  const seasonal = seasonalStats(data)

  // 24小时
  echarts.init(hourChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0 },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: hourly.map((h) => h.hour + '时'), axisLabel },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { name: 'PM2.5', type: 'line', smooth: true, data: hourly.map((h) => h.pm25), itemStyle: { color: '#ee6666' }, areaStyle: { color: 'rgba(238,102,102,0.08)' }, markPoint: { data: [{ type: 'max', name: '峰值' }, { type: 'min', name: '谷值' }] } },
      { name: 'PM10', type: 'line', smooth: true, data: hourly.map((h) => h.pm10), itemStyle: { color: '#5470c6' } }
    ]
  })

  // 周变化
  echarts.init(weekChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0 },
    grid: { left: 45, right: 20, top: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: weekly.map((w) => w.day),
      axisLabel: {
        color: (v) => {
          const item = weekly.find((w) => w.day === v)
          return item?.isWeekend ? '#ee6666' : '#909399'
        }
      }
    },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { name: 'PM2.5', type: 'bar', data: weekly.map((w) => w.pm25), itemStyle: { color: '#ee6666' }, barGap: '10%' },
      { name: 'PM10', type: 'bar', data: weekly.map((w) => w.pm10), itemStyle: { color: '#5470c6' } }
    ]
  })

  // 季节
  echarts.init(seasonChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0 },
    grid: { left: 45, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: seasonal.map((s) => s.name), axisLabel },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { name: 'PM2.5', type: 'bar', data: seasonal.map((s) => s.pm25), itemStyle: { color: '#91cc75' } },
      { name: 'PM10', type: 'bar', data: seasonal.map((s) => s.pm10), itemStyle: { color: '#fac858' } }
    ]
  })

  // 月度
  echarts.init(monthChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0 },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: monthly.map((m) => m.month + '月'), axisLabel },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { name: 'PM2.5', type: 'line', smooth: true, data: monthly.map((m) => m.pm25), itemStyle: { color: '#ee6666' }, lineStyle: { width: 2 } },
      { name: 'PM10', type: 'line', smooth: true, data: monthly.map((m) => m.pm10), itemStyle: { color: '#5470c6' }, lineStyle: { width: 2 } }
    ]
  })

  window.addEventListener('resize', () => {
    ;[hourChart, weekChart, monthChart, seasonChart].forEach((r) => echarts.getInstanceByDom(r.value)?.resize())
  })
})
</script>

<style scoped>
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
  margin-bottom: 20px;
}
.flex-1 {
  flex: 1;
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  display: inline-block;
  width: 4px;
  height: 16px;
  background: #2b7cff;
  border-radius: 2px;
}
.chart {
  width: 100%;
  height: 360px;
}
.chart-md {
  width: 100%;
  height: 300px;
}
.insight {
  margin-top: 14px;
  padding: 12px 16px;
  background: #f0f7ff;
  border-left: 3px solid #2b7cff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
</style>
