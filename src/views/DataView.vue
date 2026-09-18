<template>
  <div class="page">
    <div class="page-header">
      <h2>原始数据</h2>
      <p class="subtitle">小时级监测数据查询与浏览</p>
    </div>

    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-item">
          <label>起始日期</label>
          <input type="date" v-model="filters.startDate" />
        </div>
        <div class="filter-item">
          <label>结束日期</label>
          <input type="date" v-model="filters.endDate" />
        </div>
        <div class="filter-item">
          <label>PM2.5 范围</label>
          <div class="range-input">
            <input type="number" v-model.number="filters.pm25Min" placeholder="最小" />
            <span>~</span>
            <input type="number" v-model.number="filters.pm25Max" placeholder="最大" />
          </div>
        </div>
        <div class="filter-item">
          <label>PM10 范围</label>
          <div class="range-input">
            <input type="number" v-model.number="filters.pm10Min" placeholder="最小" />
            <span>~</span>
            <input type="number" v-model.number="filters.pm10Max" placeholder="最大" />
          </div>
        </div>
        <div class="filter-actions">
          <button class="btn btn-primary" @click="applyFilter">查询</button>
          <button class="btn" @click="resetFilter">重置</button>
        </div>
      </div>
    </div>

    <div class="result-bar">
      <span>共 <b>{{ filtered.length.toLocaleString() }}</b> 条记录</span>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
    </div>

    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th style="width: 60px;">序号</th>
            <th>监测时间</th>
            <th>PM2.5 (μg/m³)</th>
            <th>PM10 (μg/m³)</th>
            <th>PM2.5/PM10</th>
            <th>粗颗粒物</th>
            <th>空气质量</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, idx) in pageData" :key="item.datetime">
            <td>{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
            <td>{{ item.datetime }}</td>
            <td>{{ item.pm25 }}</td>
            <td>{{ item.pm10 }}</td>
            <td>{{ item.ratio.toFixed(3) }}</td>
            <td>{{ item.coarse }}</td>
            <td>
              <span class="grade-tag" :style="{ background: grade(item.pm25).color }">
                {{ grade(item.pm25).label }}
              </span>
            </td>
          </tr>
          <tr v-if="!pageData.length">
            <td colspan="7" class="empty">暂无符合条件的数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button class="btn" :disabled="currentPage === 1" @click="currentPage = 1">首页</button>
      <button class="btn" :disabled="currentPage === 1" @click="currentPage--">上一页</button>
      <span class="page-num" v-for="p in pageNumbers" :key="p" :class="{ active: p === currentPage }" @click="currentPage = p">{{ p }}</span>
      <button class="btn" :disabled="currentPage === totalPages" @click="currentPage++">下一页</button>
      <button class="btn" :disabled="currentPage === totalPages" @click="currentPage = totalPages">末页</button>
      <select v-model.number="pageSize" class="page-size" @change="currentPage = 1">
        <option :value="50">50 条/页</option>
        <option :value="100">100 条/页</option>
        <option :value="200">200 条/页</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { loadData, gradePM25 } from '../utils/data'

const allData = ref([])
const filters = ref({ startDate: '', endDate: '', pm25Min: '', pm25Max: '', pm10Min: '', pm10Max: '' })
const applied = ref({ ...filters.value })
const currentPage = ref(1)
const pageSize = ref(100)

const grade = (v) => gradePM25(v)

const filtered = computed(() => {
  const f = applied.value
  return allData.value.filter((d) => {
    if (f.startDate && d.date < f.startDate) return false
    if (f.endDate && d.date > f.endDate) return false
    if (f.pm25Min !== '' && d.pm25 < f.pm25Min) return false
    if (f.pm25Max !== '' && d.pm25 > f.pm25Max) return false
    if (f.pm10Min !== '' && d.pm10 < f.pm10Min) return false
    if (f.pm10Max !== '' && d.pm10 > f.pm10Max) return false
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const pageData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  const pages = []
  const start = Math.max(1, cur - 2)
  const end = Math.min(total, start + 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

watch(pageSize, () => { currentPage.value = 1 })

const applyFilter = () => {
  applied.value = { ...filters.value }
  currentPage.value = 1
}
const resetFilter = () => {
  filters.value = { startDate: '', endDate: '', pm25Min: '', pm25Max: '', pm10Min: '', pm10Max: '' }
  applied.value = { ...filters.value }
  currentPage.value = 1
}

onMounted(async () => {
  allData.value = await loadData()
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

.filter-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
}
.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}
.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.filter-item label {
  font-size: 12px;
  color: #909399;
}
.filter-item input {
  padding: 6px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  width: 150px;
}
.filter-item input:focus {
  border-color: #2b7cff;
}
.range-input {
  display: flex;
  align-items: center;
  gap: 6px;
}
.range-input input {
  width: 70px;
}
.filter-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.btn {
  padding: 7px 18px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s;
}
.btn:hover:not(:disabled) {
  border-color: #2b7cff;
  color: #2b7cff;
}
.btn-primary {
  background: #2b7cff;
  color: #fff;
  border-color: #2b7cff;
}
.btn-primary:hover {
  background: #1e6ae0;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #606266;
}
.result-bar b {
  color: #2b7cff;
}
.page-info {
  color: #909399;
}

.table-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
thead {
  background: #f5f7fa;
}
th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #606266;
  border-bottom: 1px solid #ebeef5;
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #f5f7fa;
  color: #303133;
}
tbody tr:hover {
  background: #f5f9ff;
}
.empty {
  text-align: center;
  color: #c0c4cc;
  padding: 40px !important;
}
.grade-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  color: #333;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 18px;
}
.page-num {
  min-width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
}
.page-num:hover {
  border-color: #2b7cff;
  color: #2b7cff;
}
.page-num.active {
  background: #2b7cff;
  color: #fff;
  border-color: #2b7cff;
}
.page-size {
  padding: 6px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  margin-left: 10px;
}
</style>
