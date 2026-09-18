import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import DataView from '../views/DataView.vue'
import TrendView from '../views/TrendView.vue'
import CorrelationView from '../views/CorrelationView.vue'
import SourceView from '../views/SourceView.vue'
import PredictView from '../views/PredictView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView, meta: { title: '数据概览' } },
  { path: '/data', name: 'data', component: DataView, meta: { title: '原始数据' } },
  { path: '/trend', name: 'trend', component: TrendView, meta: { title: '趋势分析' } },
  { path: '/correlation', name: 'correlation', component: CorrelationView, meta: { title: '关联分析' } },
  { path: '/source', name: 'source', component: SourceView, meta: { title: '成因分析' } },
  { path: '/predict', name: 'predict', component: PredictView, meta: { title: '浓度预测' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
