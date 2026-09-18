<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-icon">🌊</div>
        <div class="logo-text">
          <h1>青岛大气</h1>
          <p>PM2.5 / PM10 分析系统</p>
        </div>
      </div>
      <nav class="nav">
        <router-link
          v-for="item in menus"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.name }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <p>数据周期：2021-2026</p>
        <p>小时级监测数据</p>
      </div>
    </aside>
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
const menus = [
  { path: '/', name: '数据概览', icon: '📊' },
  { path: '/data', name: '原始数据', icon: '📋' },
  { path: '/trend', name: '趋势分析', icon: '📈' },
  { path: '/correlation', name: '关联分析', icon: '🔗' },
  { path: '/source', name: '成因分析', icon: '🔬' },
  { path: '/predict', name: '浓度预测', icon: '🎯' }
]
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 230px;
  background: linear-gradient(180deg, #1a3a5c 0%, #0f243a 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  padding: 22px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  font-size: 32px;
  line-height: 1;
}

.logo-text h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.logo-text p {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  margin: 2px 0 0;
}

.nav {
  flex: 1;
  padding: 12px 10px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 4px;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background: linear-gradient(90deg, #2b7cff, #1e6ae0);
  color: #fff;
  box-shadow: 0 2px 8px rgba(43, 124, 255, 0.4);
}

.nav-icon {
  font-size: 18px;
}

.sidebar-footer {
  padding: 16px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  line-height: 1.8;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
