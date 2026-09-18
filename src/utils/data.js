import Papa from 'papaparse'

let rawData = null
let loadingPromise = null

// 加载并解析 CSV（带缓存）
export function loadData() {
  if (rawData) return Promise.resolve(rawData)
  if (loadingPromise) return loadingPromise

  loadingPromise = fetch('/data_pm_filled.csv')
    .then((res) => res.text())
    .then((text) => {
      const result = Papa.parse(text, {
        header: true,
        skipEmptyLines: true
      })
      rawData = result.data
        .map((row) => {
          const dt = new Date(row.datetime.trim().replace(' ', 'T'))
          const pm25 = Number(row['PM2.5 '] || row['PM2.5'])
          const pm10 = Number(row['PM10 '] || row['PM10'])
          if (isNaN(pm25) || isNaN(pm10) || isNaN(dt.getTime())) return null
          return {
            datetime: row.datetime.trim(),
            date: row.datetime.trim().slice(0, 10),
            hour: dt.getHours(),
            weekday: dt.getDay(), // 0=周日
            month: dt.getMonth() + 1,
            year: dt.getFullYear(),
            pm25,
            pm10,
            ratio: pm10 > 0 ? pm25 / pm10 : 0,
            coarse: pm10 - pm25 > 0 ? pm10 - pm25 : 0
          }
        })
        .filter(Boolean)
      return rawData
    })

  return loadingPromise
}

// 数组平均
function avg(arr) {
  if (!arr.length) return 0
  return arr.reduce((a, b) => a + b, 0) / arr.length
}

// 皮尔逊相关系数
export function pearson(xs, ys) {
  const n = xs.length
  if (n < 2) return 0
  const mx = avg(xs)
  const my = avg(ys)
  let num = 0
  let dx = 0
  let dy = 0
  for (let i = 0; i < n; i++) {
    const a = xs[i] - mx
    const b = ys[i] - my
    num += a * b
    dx += a * a
    dy += b * b
  }
  return dx && dy ? num / Math.sqrt(dx * dy) : 0
}

// 24小时日变化（按小时聚合）
export function hourlyStats(data) {
  const buckets = Array.from({ length: 24 }, () => ({ pm25: [], pm10: [], ratio: [], coarse: [] }))
  data.forEach((d) => {
    buckets[d.hour].pm25.push(d.pm25)
    buckets[d.hour].pm10.push(d.pm10)
    buckets[d.hour].ratio.push(d.ratio)
    buckets[d.hour].coarse.push(d.coarse)
  })
  return buckets.map((b, h) => ({
    hour: h,
    pm25: +avg(b.pm25).toFixed(1),
    pm10: +avg(b.pm10).toFixed(1),
    ratio: +avg(b.ratio).toFixed(3),
    coarse: +avg(b.coarse).toFixed(1)
  }))
}

// 周变化（0=周日 ... 6=周六），返回周一到周日顺序
export function weeklyStats(data) {
  const names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const buckets = Array.from({ length: 7 }, () => ({ pm25: [], pm10: [] }))
  data.forEach((d) => {
    buckets[d.weekday].pm25.push(d.pm25)
    buckets[d.weekday].pm10.push(d.pm10)
  })
  // 按周一到周日排列
  const order = [1, 2, 3, 4, 5, 6, 0]
  return order.map((i) => ({
    day: names[i],
    isWeekend: i === 0 || i === 6,
    pm25: +avg(buckets[i].pm25).toFixed(1),
    pm10: +avg(buckets[i].pm10).toFixed(1)
  }))
}

// 月变化
export function monthlyStats(data) {
  const buckets = Array.from({ length: 12 }, () => ({ pm25: [], pm10: [] }))
  data.forEach((d) => {
    buckets[d.month - 1].pm25.push(d.pm25)
    buckets[d.month - 1].pm10.push(d.pm10)
  })
  return buckets.map((b, i) => ({
    month: i + 1,
    pm25: +avg(b.pm25).toFixed(1),
    pm10: +avg(b.pm10).toFixed(1)
  }))
}

// 季节变化（3-5春,6-8夏,9-11秋,12-2冬）
export function seasonalStats(data) {
  const seasons = [
    { name: '春季', months: [3, 4, 5], pm25: [], pm10: [] },
    { name: '夏季', months: [6, 7, 8], pm25: [], pm10: [] },
    { name: '秋季', months: [9, 10, 11], pm25: [], pm10: [] },
    { name: '冬季', months: [12, 1, 2], pm25: [], pm10: [] }
  ]
  data.forEach((d) => {
    const s = seasons.find((s) => s.months.includes(d.month))
    s.pm25.push(d.pm25)
    s.pm10.push(d.pm10)
  })
  return seasons.map((s) => ({
    name: s.name,
    pm25: +avg(s.pm25).toFixed(1),
    pm10: +avg(s.pm10).toFixed(1)
  }))
}

// 日均值序列（用于趋势图，降采样）
export function dailyAverages(data) {
  const map = new Map()
  data.forEach((d) => {
    if (!map.has(d.date)) map.set(d.date, { pm25: [], pm10: [] })
    map.get(d.date).pm25.push(d.pm25)
    map.get(d.date).pm10.push(d.pm10)
  })
  const result = []
  for (const [date, v] of map) {
    result.push({
      date,
      pm25: +avg(v.pm25).toFixed(1),
      pm10: +avg(v.pm10).toFixed(1)
    })
  }
  result.sort((a, b) => a.date.localeCompare(b.date))
  return result
}

// 污染等级（基于 PM2.5 日均，参照 GB 3095-2012）
export function gradePM25(v) {
  if (v <= 35) return { label: '优', color: '#00e400' }
  if (v <= 75) return { label: '良', color: '#ffff00' }
  if (v <= 115) return { label: '轻度污染', color: '#ff7e00' }
  if (v <= 150) return { label: '中度污染', color: '#ff0000' }
  if (v <= 250) return { label: '重度污染', color: '#99004c' }
  return { label: '严重污染', color: '#7e0023' }
}

// 基于日均值的等级分布
export function gradeDistribution(daily) {
  const counts = { 优: 0, 良: 0, 轻度污染: 0, 中度污染: 0, 重度污染: 0, 严重污染: 0 }
  daily.forEach((d) => {
    counts[gradePM25(d.pm25).label]++
  })
  return Object.entries(counts).map(([name, value]) => ({ name, value }))
}

// PM2.5/PM10 比值区间分布
export function ratioDistribution(data) {
  const bins = [
    { name: '<0.4 (自然/机械源)', min: 0, max: 0.4, count: 0 },
    { name: '0.4-0.6 (混合源)', min: 0.4, max: 0.6, count: 0 },
    { name: '>0.6 (人为源/二次生成)', min: 0.6, max: Infinity, count: 0 }
  ]
  data.forEach((d) => {
    const b = bins.find((b) => d.ratio >= b.min && d.ratio < b.max)
    if (b) b.count++
  })
  return bins.map((b) => ({ name: b.name, value: b.count }))
}

// 工作日 vs 周末对比（按小时）
export function workdayVsWeekend(data) {
  const work = data.filter((d) => d.weekday >= 1 && d.weekday <= 5)
  const weekend = data.filter((d) => d.weekday === 0 || d.weekday === 6)
  return {
    workHourly: hourlyStats(work),
    weekendHourly: hourlyStats(weekend),
    workAvgPm25: +avg(work.map((d) => d.pm25)).toFixed(1),
    weekendAvgPm25: +avg(weekend.map((d) => d.pm25)).toFixed(1),
    workAvgPm10: +avg(work.map((d) => d.pm10)).toFixed(1),
    weekendAvgPm10: +avg(weekend.map((d) => d.pm10)).toFixed(1)
  }
}

// 汇总统计
export function summaryStats(data) {
  const pm25s = data.map((d) => d.pm25)
  const pm10s = data.map((d) => d.pm10)
  const sorted25 = [...pm25s].sort((a, b) => a - b)
  const p = (arr, q) => arr[Math.floor(arr.length * q)] || 0
  return {
    total: data.length,
    startDate: data[0].date,
    endDate: data[data.length - 1].date,
    pm25Avg: +avg(pm25s).toFixed(1),
    pm10Avg: +avg(pm10s).toFixed(1),
    pm25Max: Math.max(...pm25s),
    pm10Max: Math.max(...pm10s),
    pm25Min: Math.min(...pm25s),
    pm10Min: Math.min(...pm10s),
    pm25Median: +p(sorted25, 0.5).toFixed(1),
    ratioAvg: +avg(data.map((d) => d.ratio)).toFixed(3),
    pearson: +pearson(pm25s, pm10s).toFixed(3)
  }
}
