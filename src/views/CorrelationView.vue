<template>
  <div class="page">
    <div class="page-header">
      <h2>关联分析</h2>
      <p class="subtitle">PM2.5 与 PM10 的相关性及空气质量等级分布</p>
    </div>

    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-num" style="color:#ee6666">{{ r }}</div>
        <div class="stat-label">皮尔逊相关系数 r</div>
        <div class="stat-desc">{{ corrLevel }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:#2b7cff">{{ r2 }}</div>
        <div class="stat-label">决定系数 R²</div>
        <div class="stat-desc">PM10 可解释 PM2.5 {{ r2Percent }} 的变异</div>
      </div>
      <div class="stat-card">
        <div class="stat-num" style="color:#91cc75">{{ goodPercent }}%</div>
        <div class="stat-label">优良天数占比</div>
        <div class="stat-desc">基于日均 PM2.5 评估</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span class="dot"></span>PM2.5 与 PM10 散点相关性分析（日均值）</div>
      <div ref="scatterChart" class="chart-lg"></div>
      <div class="insight">
        <b>📌 分析：</b>散点紧密分布于对角线附近，皮尔逊相关系数达 <b>{{ r }}</b>，表明 PM2.5 与 PM10 具有高度正相关，
        二者具有显著的同源性与变化一致性，主要受相同的污染源与气象扩散条件影响。
      </div>
    </div>

    <div class="card-row">
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>空气质量等级分布</div>
        <div ref="gradeBarChart" class="chart-md"></div>
      </div>
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>等级占比</div>
        <div ref="gradePieChart" class="chart-md"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import { loadData, dailyAverages, gradeDistribution, pearson } from '../utils/data'

const scatterChart = ref(null)
const gradeBarChart = ref(null)
const gradePieChart = ref(null)

const r = ref(0)
const r2 = computed(() => (r.value ** 2).toFixed(3))
const r2Percent = computed(() => (r.value ** 2 * 100).toFixed(1) + '%')
const goodPercent = ref(0)

const corrLevel = computed(() => {
  const v = Math.abs(r.value)
  if (v >= 0.8) return '强正相关（高度同源）'
  if (v >= 0.5) return '中等正相关'
  if (v >= 0.3) return '弱正相关'
  return '相关性较弱'
})

const axisLabel = { color: '#909399' }
const splitLine = { lineStyle: { color: '#f0f0f0' } }

const pieColors = {
  优: '#00e400',
  良: '#c9c900',
  轻度污染: '#ff7e00',
  中度污染: '#ff0000',
  重度污染: '#99004c',
  严重污染: '#7e0023'
}

onMounted(async () => {
  const data = await loadData()
  const daily = dailyAverages(data)
  const xs = daily.map((d) => d.pm25)
  const ys = daily.map((d) => d.pm10)
  r.value = pearson(xs, ys)

  const grades = gradeDistribution(daily)
  const goodTotal = grades.filter((g) => g.name === '优' || g.name === '良').reduce((a, b) => a + b.value, 0)
  const allTotal = grades.reduce((a, b) => a + b.value, 0)
  goodPercent.value = ((goodTotal / allTotal) * 100).toFixed(1)

  const scatterData = daily.map((d) => [d.pm25, d.pm10])

  // 线性回归 y = ax + b
  const n = xs.length
  const mx = xs.reduce((a, b) => a + b, 0) / n
  const my = ys.reduce((a, b) => a + b, 0) / n
  let num = 0, den = 0
  for (let i = 0; i < n; i++) {
    num += (xs[i] - mx) * (ys[i] - my)
    den += (xs[i] - mx) ** 2
  }
  const a = num / den
  const b = my - a * mx
  const xMin = Math.min(...xs)
  const xMax = Math.max(...xs)

  echarts.init(scatterChart.value).setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => `PM2.5: ${p.value[0]} μg/m³<br/>PM10: ${p.value[1]} μg/m³`
    },
    grid: { left: 60, right: 40, top: 40, bottom: 50 },
    xAxis: { name: 'PM2.5 (μg/m³)', type: 'value', axisLabel, splitLine, nameLocation: 'middle', nameGap: 30 },
    yAxis: { name: 'PM10 (μg/m³)', type: 'value', axisLabel, splitLine },
    series: [
      {
        type: 'scatter',
        data: scatterData,
        symbolSize: 5,
        itemStyle: { color: 'rgba(43,124,255,0.4)' },
        large: true
      },
      {
        type: 'line',
        data: [[xMin, a * xMin + b], [xMax, a * xMax + b]],
        showSymbol: false,
        lineStyle: { color: '#ee6666', width: 2, type: 'dashed' },
        tooltip: { show: false }
      }
    ]
  })

  echarts.init(gradeBarChart.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 20, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: grades.map((g) => g.name), axisLabel: { ...axisLabel, rotate: 20, fontSize: 11 } },
    yAxis: { type: 'value', name: '天数', axisLabel, splitLine },
    series: [
      {
        type: 'bar',
        data: grades.map((g) => ({ value: g.value, itemStyle: { color: pieColors[g.name] } })),
        barWidth: '50%',
        label: { show: true, position: 'top', fontSize: 11, color: '#606266' }
      }
    ]
  })

  echarts.init(gradePieChart.value).setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 天 ({d}%)' },
    legend: { bottom: 0, textStyle: { color: '#606266', fontSize: 11 } },
    series: [
      {
        type: 'pie',
        radius: ['40%', '68%'],
        center: ['50%', '45%'],
        label: { formatter: '{d}%', fontSize: 11 },
        data: grades.map((g) => ({ name: g.name, value: g.value, itemStyle: { color: pieColors[g.name] } }))
      }
    ]
  })

  window.addEventListener('resize', () => {
    ;[scatterChart, gradeBarChart, gradePieChart].forEach((r) => echarts.getInstanceByDom(r.value)?.resize())
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
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.stat-num {
  font-size: 36px;
  font-weight: 700;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}
.stat-desc {
  font-size: 12px;
  color: #c0c4cc;
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
.chart-lg {
  width: 100%;
  height: 420px;
}
.chart-md {
  width: 100%;
  height: 320px;
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
