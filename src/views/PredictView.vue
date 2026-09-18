<template>
  <div class="page">
    <div class="page-header">
      <h2>浓度预测</h2>
      <p class="subtitle">基于深度学习模型（LSTM / GRU / CNN-LSTM / Attention-LSTM）预测未来 PM2.5 与 PM10 浓度</p>
    </div>

    <div class="predict-card">
      <div class="input-area">
        <div class="form-item">
          <label>预测起始日期</label>
          <input type="date" v-model="predictDate" />
        </div>
        <div class="form-item">
          <label>预测模型</label>
          <select v-model="model">
            <option v-for="m in modelList" :key="m.key" :value="m.key">{{ m.label }}</option>
          </select>
        </div>
        <div class="form-item">
          <label>预测天数</label>
          <select v-model.number="days">
            <option :value="1">未来 1 天</option>
            <option :value="3">未来 3 天</option>
            <option :value="7">未来 7 天</option>
          </select>
        </div>
        <button class="btn-predict" :disabled="loading" @click="doPredict">
          {{ loading ? '预测中...' : '🔮 执行预测' }}
        </button>
      </div>
      <div class="model-tip">
        <span v-if="backendStatus === 'online'" class="status status-online">● 已连接模型服务（真实模型推理）</span>
        <span v-else-if="backendStatus === 'connecting'" class="status status-connecting">● 正在连接模型服务...</span>
        <span v-else-if="backendStatus === 'offline'" class="status status-fallback">● 后端未连接，请启动模型服务</span>
        <span v-else class="status status-loading">● 正在检查模型服务...</span>
        <span v-if="result" class="data-range">数据范围：{{ result.data_range.start }} ~ {{ result.data_range.end }}</span>
      </div>
    </div>

    <!-- 模型指标 -->
    <div v-if="modelMetrics" class="metrics-row">
      <div class="metric-card">
        <div class="metric-title">{{ currentModelLabel }}</div>
        <div class="metric-grid">
          <div class="metric-item">
            <span class="metric-label">PM2.5 MAE</span>
            <span class="metric-val">{{ modelMetrics.pm25_mae }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PM2.5 RMSE</span>
            <span class="metric-val">{{ modelMetrics.pm25_rmse }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PM2.5 R²</span>
            <span class="metric-val">{{ modelMetrics.pm25_r2 }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PM10 MAE</span>
            <span class="metric-val">{{ modelMetrics.pm10_mae }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PM10 RMSE</span>
            <span class="metric-val">{{ modelMetrics.pm10_rmse }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PM10 R²</span>
            <span class="metric-val">{{ modelMetrics.pm10_r2 }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="result" class="result-row">
      <div v-for="(day, idx) in result.daily" :key="idx" class="result-card" :class="{ 'first-day': idx === 0 }">
        <div class="result-label">预测日期</div>
        <div class="result-date">{{ day.date }}</div>
        <div class="weekday">{{ weekdayOf(day.date) }}</div>
        <div class="pm-row">
          <div class="pm-block pm25">
            <span class="pm-num">{{ day.pm25 }}</span>
            <span class="pm-tag">PM2.5</span>
          </div>
          <div class="pm-block pm10">
            <span class="pm-num">{{ day.pm10 }}</span>
            <span class="pm-tag">PM10</span>
          </div>
        </div>
        <div class="grade-tag" :style="{ background: gradePM25(day.pm25).color }">
          {{ gradePM25(day.pm25).label }}
        </div>
      </div>
    </div>

    <div v-if="result" class="card">
      <div class="card-title"><span class="dot"></span>逐时浓度预测曲线</div>
      <div ref="hourlyChart" class="chart"></div>
      <div class="insight">
        <b>📌 预测说明：</b>模型输入为预测时刻前 24 小时的 46 维特征（污染物浓度、滞后特征、滑动统计、时间周期等），
        经 MinMaxScaler 归一化后由深度学习模型推理，再反归一化得到预测浓度。超出历史数据范围的日期采用自回归多步预测。
      </div>
    </div>

    <div v-if="result" class="card">
      <div class="card-title"><span class="dot"></span>历史趋势与预测对比</div>
      <div ref="forecastChart" class="chart"></div>
    </div>

    <div class="card info-card">
      <div class="card-title"><span class="dot"></span>模型架构说明</div>
      <div class="model-grid">
        <div class="model-item">
          <h4>LSTM / GRU 基线</h4>
          <p>两层循环神经网络，隐藏层 64 维，捕捉污染物浓度的时序依赖与滞后效应，作为对比基准。</p>
        </div>
        <div class="model-item">
          <h4>CNN-LSTM</h4>
          <p>Conv1d（kernel=3, padding=1）+ ReLU 提取局部时序特征，再经两层 LSTM 建模长时依赖。</p>
        </div>
        <div class="model-item highlight">
          <h4>Attention-LSTM ⭐</h4>
          <p>在两层 LSTM 之上引入加性注意力（Bahdanau），自动加权关键历史时刻，对污染累积与消散更敏感。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { loadData, dailyAverages, gradePM25 } from '../utils/data'

const predictDate = ref('')
const model = ref('att_lstm')
const days = ref(1)
const loading = ref(false)
const result = ref(null)
const backendStatus = ref('checking')
const modelList = ref([])
const modelMetricsMap = ref({})
const hourlyChart = ref(null)
const forecastChart = ref(null)
const allDaily = ref([])
let hourlyChartInst = null
let forecastChartInst = null

const currentModelLabel = computed(() => {
  const m = modelList.value.find((x) => x.key === model.value)
  return m ? m.label : model.value
})

const modelMetrics = computed(() => modelMetricsMap.value[model.value] || null)

function weekdayOf(dateStr) {
  const names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return names[new Date(dateStr).getDay()]
}

async function checkBackend(retries = 10) {
  for (let i = 0; i < retries; i++) {
    try {
      const resp = await fetch('/api/models')
      if (resp.ok) {
        const data = await resp.json()
        modelList.value = data.models || []
        const map = {}
        for (const m of data.models || []) {
          if (m.metrics && Object.keys(m.metrics).length > 0) {
            map[m.key] = m.metrics
          }
        }
        modelMetricsMap.value = map
        backendStatus.value = 'online'
        return
      }
    } catch (e) {
      // 后端未就绪，等待后重试
    }
    if (i < retries - 1) {
      backendStatus.value = 'connecting'
      await new Promise((r) => setTimeout(r, 2000))
    }
  }
  backendStatus.value = 'offline'
}

async function doPredict() {
  if (!predictDate.value) {
    alert('请选择预测日期')
    return
  }
  loading.value = true
  result.value = null

  try {
    const resp = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: predictDate.value,
        model: model.value,
        days: days.value
      })
    })
    if (resp.ok) {
      result.value = await resp.json()
      backendStatus.value = 'online'
    } else {
      backendStatus.value = 'offline'
    }
  } catch (e) {
    backendStatus.value = 'offline'
  }

  loading.value = false
  await nextTick()
  if (result.value) {
    renderHourlyChart()
    renderForecastChart()
  }
}

function renderHourlyChart() {
  if (!result.value) return
  if (hourlyChartInst) hourlyChartInst.dispose()
  hourlyChartInst = echarts.init(hourlyChart.value)

  const hourly = result.value.hourly
  const times = hourly.map((h) => h.datetime.slice(5))
  const pm25 = hourly.map((h) => h.pm25)
  const pm10 = hourly.map((h) => h.pm10)

  hourlyChartInst.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5', 'PM10'], top: 0 },
    grid: { left: 50, right: 30, top: 40, bottom: 60 },
    xAxis: {
      type: 'category',
      data: times,
      axisLabel: { color: '#909399', rotate: 45, fontSize: 10, interval: 2 },
      axisLine: { lineStyle: { color: '#e0e0e0' } }
    },
    yAxis: {
      type: 'value',
      name: 'μg/m³',
      axisLabel: { color: '#909399' },
      splitLine: { lineStyle: { color: '#f0f0f0' } }
    },
    series: [
      {
        name: 'PM2.5',
        type: 'line',
        data: pm25,
        smooth: true,
        symbol: 'none',
        itemStyle: { color: '#ee6666' },
        areaStyle: { color: 'rgba(238,102,102,0.08)' }
      },
      {
        name: 'PM10',
        type: 'line',
        data: pm10,
        smooth: true,
        symbol: 'none',
        itemStyle: { color: '#5470c6' },
        areaStyle: { color: 'rgba(84,112,198,0.08)' }
      }
    ]
  })
}

function renderForecastChart() {
  if (!result.value) return
  if (forecastChartInst) forecastChartInst.dispose()
  forecastChartInst = echarts.init(forecastChart.value)

  const history = allDaily.value.slice(-30)
  const predDates = result.value.daily.map((d) => d.date)
  const dates = [...history.map((h) => h.date), ...predDates]
  const histPm25 = history.map((h) => h.pm25)
  const histPm10 = history.map((h) => h.pm10)
  const predPm25 = result.value.daily.map((d) => d.pm25)
  const predPm10 = result.value.daily.map((d) => d.pm10)

  forecastChartInst.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['PM2.5实测', 'PM10实测', 'PM2.5预测', 'PM10预测'], top: 0 },
    grid: { left: 50, right: 30, top: 40, bottom: 60 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { color: '#909399', rotate: 30, fontSize: 11 },
      axisLine: { lineStyle: { color: '#e0e0e0' } }
    },
    yAxis: {
      type: 'value',
      name: 'μg/m³',
      axisLabel: { color: '#909399' },
      splitLine: { lineStyle: { color: '#f0f0f0' } }
    },
    series: [
      {
        name: 'PM2.5实测', type: 'line', data: [...histPm25, ...predDates.map(() => null)],
        smooth: true, symbol: 'none', itemStyle: { color: '#ee6666' }
      },
      {
        name: 'PM10实测', type: 'line', data: [...histPm10, ...predDates.map(() => null)],
        smooth: true, symbol: 'none', itemStyle: { color: '#5470c6' }
      },
      {
        name: 'PM2.5预测', type: 'line',
        data: [...histPm25.map(() => null), ...predPm25],
        symbol: 'circle', symbolSize: 8,
        lineStyle: { type: 'dashed', color: '#ee6666', width: 2 },
        itemStyle: { color: '#ee6666' }
      },
      {
        name: 'PM10预测', type: 'line',
        data: [...histPm10.map(() => null), ...predPm10],
        symbol: 'circle', symbolSize: 8,
        lineStyle: { type: 'dashed', color: '#5470c6', width: 2 },
        itemStyle: { color: '#5470c6' }
      }
    ]
  })
}

watch(model, () => {
  if (result.value) doPredict()
})

onMounted(async () => {
  allDaily.value = dailyAverages(await loadData())
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  predictDate.value = tomorrow.toISOString().slice(0, 10)
  await checkBackend()
  window.addEventListener('resize', () => {
    hourlyChartInst?.resize()
    forecastChartInst?.resize()
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

.predict-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-item label {
  font-size: 12px;
  color: #909399;
}
.form-item input,
.form-item select {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  width: 200px;
}
.form-item input:focus,
.form-item select:focus {
  border-color: #2b7cff;
}
.btn-predict {
  padding: 9px 28px;
  background: linear-gradient(90deg, #2b7cff, #1e6ae0);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(43, 124, 255, 0.4);
  transition: all 0.2s;
}
.btn-predict:hover:not(:disabled) {
  transform: translateY(-1px);
}
.btn-predict:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.model-tip {
  margin-top: 14px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.status { font-size: 12px; }
.status-online { color: #67c23a; }
.status-connecting { color: #409eff; }
.status-fallback { color: #e6a23c; }
.status-loading { color: #909399; }
.data-range { color: #c0c4cc; }

.metrics-row {
  margin-bottom: 20px;
}
.metric-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.metric-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}
.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px;
  background: #f7f9fc;
  border-radius: 6px;
}
.metric-label {
  font-size: 11px;
  color: #909399;
}
.metric-val {
  font-size: 18px;
  font-weight: 700;
  color: #2b7cff;
}

.result-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}
.result-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  text-align: center;
  border-top: 3px solid #dcdfe6;
}
.result-card.first-day {
  border-top-color: #2b7cff;
  box-shadow: 0 2px 12px rgba(43, 124, 255, 0.15);
}
.result-label {
  font-size: 12px;
  color: #909399;
}
.result-date {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin: 6px 0 2px;
}
.weekday {
  font-size: 12px;
  color: #c0c4cc;
  margin-bottom: 12px;
}
.pm-row {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 10px;
}
.pm-block {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.pm-num {
  font-size: 28px;
  font-weight: 700;
}
.pm-block.pm25 .pm-num { color: #ee6666; }
.pm-block.pm10 .pm-num { color: #5470c6; }
.pm-tag {
  font-size: 11px;
  color: #909399;
}
.grade-tag {
  display: inline-block;
  padding: 3px 14px;
  border-radius: 12px;
  font-size: 12px;
  color: #333;
}

.card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
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

.info-card { margin-top: 20px; }
.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.model-item {
  background: #f7f9fc;
  border-radius: 8px;
  padding: 14px 16px;
  border-left: 3px solid #dcdfe6;
}
.model-item h4 {
  font-size: 14px;
  color: #303133;
  margin-bottom: 6px;
}
.model-item p {
  font-size: 12px;
  color: #909399;
  line-height: 1.7;
}
.model-item.highlight {
  background: #f0f7ff;
  border-left-color: #2b7cff;
}

@media (max-width: 900px) {
  .metric-grid { grid-template-columns: repeat(3, 1fr); }
  .model-grid { grid-template-columns: 1fr; }
}
</style>
