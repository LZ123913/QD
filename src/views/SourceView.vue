<template>
  <div class="page">
    <div class="page-header">
      <h2>成因分析</h2>
      <p class="subtitle">基于比值法与人类活动规律，解析青岛沿海城市大气污染来源</p>
    </div>

    <!-- 比值法 -->
    <div class="section-title">
      <span class="bar"></span>
      <h3>一、基于比值法的污染来源类型解析</h3>
    </div>

    <div class="card">
      <div class="card-title"><span class="dot"></span>PM2.5 / PM10 比值区间分布</div>
      <div class="ratio-wrap">
        <div ref="ratioPie" class="chart-md"></div>
        <div class="ratio-legend">
          <div class="legend-item">
            <div class="legend-color" style="background:#5470c6"></div>
            <div>
              <b>比值 &lt; 0.4</b>
              <p>粗颗粒占比高，偏向扬尘、海盐粒子、风沙等自然 / 机械源</p>
            </div>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background:#91cc75"></div>
            <div>
              <b>比值 0.4 - 0.6</b>
              <p>粗细颗粒混合，人为源与自然源共同作用</p>
            </div>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background:#ee6666"></div>
            <div>
              <b>比值 &gt; 0.6</b>
              <p>细颗粒为主，偏向机动车尾气、二次生成等人为源</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card-row">
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>24 小时比值变化（早晚高峰尾气影响）</div>
        <div ref="ratioHourChart" class="chart-md"></div>
      </div>
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>月度比值变化（沿海季节性特征）</div>
        <div ref="ratioMonthChart" class="chart-md"></div>
      </div>
    </div>

    <div class="insight">
      <b>📌 比值结论：</b>早晚高峰时段 PM2.5/PM10 比值明显升高，反映机动车尾气排放使细颗粒占比上升；
      冬春季节比值相对偏低，与北方大风起尘、沿海海盐粒子贡献粗颗粒有关；夏季比值升高，二次气溶胶生成贡献增强。
    </div>

    <!-- 粗颗粒物 -->
    <div class="section-title" style="margin-top:28px">
      <span class="bar"></span>
      <h3>二、粗颗粒物（PM10 - PM2.5）变化分析</h3>
    </div>

    <div class="card-row">
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>24 小时粗颗粒物变化</div>
        <div ref="coarseHourChart" class="chart-md"></div>
      </div>
      <div class="card flex-1">
        <div class="card-title"><span class="dot"></span>月度粗颗粒物变化</div>
        <div ref="coarseMonthChart" class="chart-md"></div>
      </div>
    </div>

    <div class="insight">
      <b>📌 粗颗粒结论：</b>粗颗粒物在白天交通活跃时段及大风季节偏高，反映道路扬尘、建筑扬尘与海风携带海盐粒子的影响；
      夜间粗颗粒下降，进一步说明粗颗粒主要受机械扰动与气象因素驱动，与细颗粒的累积性污染特征不同。
    </div>

    <!-- 人类活动 -->
    <div class="section-title" style="margin-top:28px">
      <span class="bar"></span>
      <h3>三、人类活动影响：工作日 vs 周末</h3>
    </div>

    <div class="compare-row">
      <div class="compare-card">
        <div class="compare-label">工作日 PM2.5 均值</div>
        <div class="compare-value" style="color:#ee6666">{{ compare.workAvgPm25 }}</div>
        <div class="compare-label">PM10 均值：{{ compare.workAvgPm10 }} μg/m³</div>
      </div>
      <div class="compare-card">
        <div class="compare-label">周末 PM2.5 均值</div>
        <div class="compare-value" style="color:#5470c6">{{ compare.weekendAvgPm25 }}</div>
        <div class="compare-label">PM10 均值：{{ compare.weekendAvgPm10 }} μg/m³</div>
      </div>
      <div class="compare-card">
        <div class="compare-label">工作日-周末差值（PM2.5）</div>
        <div class="compare-value" :style="{color: diffColor}">{{ diffPm25 > 0 ? '+' : '' }}{{ diffPm25 }}</div>
        <div class="compare-label">{{ diffText }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span class="dot"></span>工作日与周末 24 小时浓度对比</div>
      <div ref="workChart" class="chart"></div>
      <div class="insight" style="margin-top:14px">
        <b>📌 人类活动结论：</b>工作日早高峰浓度抬升更明显，与通勤交通排放及工业活动周内节律一致；
        周末整体浓度水平与工作日存在差异，反映了人类活动强度周度变化对空气质量的直接影响。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'
import {
  loadData,
  hourlyStats,
  ratioDistribution,
  workdayVsWeekend
} from '../utils/data'

const ratioPie = ref(null)
const ratioHourChart = ref(null)
const ratioMonthChart = ref(null)
const coarseHourChart = ref(null)
const coarseMonthChart = ref(null)
const workChart = ref(null)

const compare = ref({
  workAvgPm25: 0,
  workAvgPm10: 0,
  weekendAvgPm25: 0,
  weekendAvgPm10: 0,
  workHourly: [],
  weekendHourly: []
})

const diffPm25 = computed(() => (compare.value.workAvgPm25 - compare.value.weekendAvgPm25).toFixed(1))
const diffColor = computed(() => (diffPm25.value > 0 ? '#ee6666' : '#91cc75'))
const diffText = computed(() =>
  diffPm25.value > 0 ? '工作日浓度更高，通勤排放影响显著' : '周末浓度更高，出行/工业特征不同'
)

const axisLabel = { color: '#909399' }
const splitLine = { lineStyle: { color: '#f0f0f0' } }

function monthlyAgg(data) {
  const buckets = Array.from({ length: 12 }, () => ({ ratio: [], coarse: [] }))
  data.forEach((d) => {
    buckets[d.month - 1].ratio.push(d.ratio)
    buckets[d.month - 1].coarse.push(d.coarse)
  })
  return buckets.map((b, i) => ({
    month: i + 1,
    ratio: +(b.ratio.reduce((a, c) => a + c, 0) / b.ratio.length).toFixed(3),
    coarse: +(b.coarse.reduce((a, c) => a + c, 0) / b.coarse.length).toFixed(1)
  }))
}

onMounted(async () => {
  const data = await loadData()
  const hourly = hourlyStats(data)
  const monthly = monthlyAgg(data)
  const ratioDist = ratioDistribution(data)
  const wv = workdayVsWeekend(data)
  compare.value = wv

  // 比值饼图
  echarts.init(ratioPie.value).setOption({
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 条 ({d}%)' },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        label: { formatter: '{d}%', fontSize: 12 },
        data: [
          { name: '<0.4', value: ratioDist[0].value, itemStyle: { color: '#5470c6' } },
          { name: '0.4-0.6', value: ratioDist[1].value, itemStyle: { color: '#91cc75' } },
          { name: '>0.6', value: ratioDist[2].value, itemStyle: { color: '#ee6666' } }
        ]
      }
    ]
  })

  // 24小时比值
  echarts.init(ratioHourChart.value).setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => v.toFixed(3) },
    grid: { left: 45, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: hourly.map((h) => h.hour + '时'), axisLabel: { ...axisLabel, interval: 2 } },
    yAxis: { type: 'value', name: '比值', axisLabel, splitLine },
    series: [
      {
        type: 'line',
        smooth: true,
        data: hourly.map((h) => h.ratio),
        itemStyle: { color: '#ee6666' },
        areaStyle: { color: 'rgba(238,102,102,0.1)' },
        markLine: { data: [{ yAxis: 0.6, name: '0.6' }, { yAxis: 0.4, name: '0.4' }], lineStyle: { type: 'dashed' } }
      }
    ]
  })

  // 月度比值
  echarts.init(ratioMonthChart.value).setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => v.toFixed(3) },
    grid: { left: 45, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: monthly.map((m) => m.month + '月'), axisLabel },
    yAxis: { type: 'value', name: '比值', axisLabel, splitLine },
    series: [
      { type: 'line', smooth: true, data: monthly.map((m) => m.ratio), itemStyle: { color: '#91cc75' }, areaStyle: { color: 'rgba(145,204,117,0.1)' } }
    ]
  })

  // 24小时粗颗粒
  echarts.init(coarseHourChart.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: hourly.map((h) => h.hour + '时'), axisLabel: { ...axisLabel, interval: 2 } },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { type: 'bar', data: hourly.map((h) => h.coarse), itemStyle: { color: '#fac858' }, barWidth: '60%' }
    ]
  })

  // 月度粗颗粒
  echarts.init(coarseMonthChart.value).setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 45, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: monthly.map((m) => m.month + '月'), axisLabel },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { type: 'bar', data: monthly.map((m) => m.coarse), itemStyle: { color: '#73c0de' }, barWidth: '50%' }
    ]
  })

  // 工作日vs周末
  echarts.init(workChart.value).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['工作日PM2.5', '周末PM2.5', '工作日PM10', '周末PM10'], top: 0 },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: wv.workHourly.map((h) => h.hour + '时'), axisLabel: { ...axisLabel, interval: 1 } },
    yAxis: { type: 'value', name: 'μg/m³', axisLabel, splitLine },
    series: [
      { name: '工作日PM2.5', type: 'line', smooth: true, data: wv.workHourly.map((h) => h.pm25), itemStyle: { color: '#ee6666' }, lineStyle: { width: 2 } },
      { name: '周末PM2.5', type: 'line', smooth: true, data: wv.weekendHourly.map((h) => h.pm25), itemStyle: { color: '#ee6666' }, lineStyle: { width: 2, type: 'dashed' } },
      { name: '工作日PM10', type: 'line', smooth: true, data: wv.workHourly.map((h) => h.pm10), itemStyle: { color: '#5470c6' }, lineStyle: { width: 2 } },
      { name: '周末PM10', type: 'line', smooth: true, data: wv.weekendHourly.map((h) => h.pm10), itemStyle: { color: '#5470c6' }, lineStyle: { width: 2, type: 'dashed' } }
    ]
  })

  window.addEventListener('resize', () => {
    ;[ratioPie, ratioHourChart, ratioMonthChart, coarseHourChart, coarseMonthChart, workChart].forEach((r) =>
      echarts.getInstanceByDom(r.value)?.resize()
    )
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
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0 16px;
}
.section-title .bar {
  width: 4px;
  height: 18px;
  background: #2b7cff;
  border-radius: 2px;
}
.section-title h3 {
  font-size: 16px;
  color: #303133;
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
.ratio-wrap {
  display: flex;
  align-items: center;
  gap: 24px;
}
.ratio-wrap .chart-md {
  flex: 1;
}
.ratio-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.legend-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  margin-top: 3px;
  flex-shrink: 0;
}
.legend-item b {
  font-size: 14px;
  color: #303133;
}
.legend-item p {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.6;
}
.insight {
  padding: 12px 16px;
  background: #f0f7ff;
  border-left: 3px solid #2b7cff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
.compare-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.compare-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.compare-label {
  font-size: 13px;
  color: #909399;
}
.compare-value {
  font-size: 34px;
  font-weight: 700;
  margin: 8px 0;
}
</style>
