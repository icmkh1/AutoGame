<script setup lang="ts">
import { ref, onMounted, onUnmounted, provide } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Filelist from './components/Filelist.vue'
import Settings from './components/Settings.vue'
import Logeditor from './components/Logeditor.vue'
import Screencast from './components/Screencast.vue'
import './App.css'

type Theme = 'light' | 'dark'
type KeymouseSubView = {
  view: 'list' | 'editor'
  fileName: string
  content: string
}

const currentView = ref('hidden')
const isMaximized = ref(false)
const currentTheme = ref<Theme>('dark')
const hasNewLogError = ref(false)
const appInfo = ref({ name: 'AutoGame', version: '0.0.0', homepage: '', instructions: '' })
let logCheckInterval: number | null = null

// 保存 keymouse 视图的子状态
const keymouseSubView = ref<KeymouseSubView>({
  view: 'list',
  fileName: '',
  content: ''
})

const themeColors = {
  light: {
    bg: '#E0E9FF',
    bgSecondary: '#E5DFE6',
    bgTertiary: '#D9D2DA',
    text: '#1F2430',
    textSecondary: '#4A5060',
    hover: 'rgba(0, 0, 0, 0.08)'
  },
  dark: {
    bg: '#1F2430',
    bgSecondary: '#1a1a2e',
    bgTertiary: '#0f0f1a',
    text: '#e0e0e0',
    textSecondary: '#9ca3af',
    hover: 'rgba(255, 255, 255, 0.08)'
  }
}

async function loadConfig() {
  try {
    const config = await (window as any).pywebview.api.get_config_file()
    if (config.theme && (config.theme === 'light' || config.theme === 'dark')) {
      currentTheme.value = config.theme
    }
  } catch (e) {
    console.error('Failed to load config:', e)
  }
}

async function loadAppInfo() {
  try {
    const info = await (window as any).pywebview.api.get_app_info()
    appInfo.value = info
  } catch (e) {
    console.error('Failed to load app info:', e)
  }
}

async function saveTheme(theme: Theme) {
  try {
    const config = await (window as any).pywebview.api.get_config_file()
    config.theme = theme
    await (window as any).pywebview.api.save_config_file(config)
  } catch (e) {
    console.error('Failed to save config:', e)
  }
}

function toggleTheme() {
  currentTheme.value = currentTheme.value === 'dark' ? 'light' : 'dark'
  saveTheme(currentTheme.value)
}

async function checkNewLogError() {
  try {
    if ((window as any).pywebview && (window as any).pywebview.api) {
      hasNewLogError.value = await (window as any).pywebview.api.has_new_error()
    }
  } catch (e) {
    console.error('Failed to check new log error:', e)
  }
}

async function clearNewLogErrorFlag() {
  try {
    if ((window as any).pywebview && (window as any).pywebview.api) {
      await (window as any).pywebview.api.clear_new_error_flag()
      hasNewLogError.value = false
    }
  } catch (e) {
    console.error('Failed to clear new log error flag:', e)
  }
}

function handleNavigate(id: string) {
  currentView.value = id
  if (id === 'logs') {
    clearNewLogErrorFlag()
  }
}

async function minimize() {
  await (window as any).pywebview.api.minimize()
}

async function toggleMaximize() {
  isMaximized.value = await (window as any).pywebview.api.toggle_maximize()
}

async function close() {
  await (window as any).pywebview.api.close()
}

async function pollForConfig() {
  const maxAttempts = 50
  let attempts = 0

  while (attempts < maxAttempts) {
    try {
      if ((window as any).pywebview && (window as any).pywebview.api) {
        await loadConfig()
        await loadAppInfo()
        return
      }
    } catch (e) {
      // 继续尝试
    }
    attempts++
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  console.warn('Failed to load config after multiple attempts')
}

onMounted(() => {
  pollForConfig()
  // 每秒检查一次是否有新的错误
  logCheckInterval = window.setInterval(checkNewLogError, 1000)
})

onUnmounted(() => {
  if (logCheckInterval !== null) {
    clearInterval(logCheckInterval)
  }
})

provide('theme', currentTheme)
provide('themeColors', themeColors)
provide('toggleTheme', toggleTheme)
provide('appInfo', appInfo)
</script>

<style src="./App.css" scoped></style>

<template>
  <div class="app-container" :data-theme="currentTheme">
    <div class="title-bar pywebview-drag-region">
      <span class="app-name">{{ appInfo.name }}</span>
      <div class="title"></div>
      <div class="window-controls">
        <button class="control-btn minimize-btn" @click="minimize">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="4" y="12" width="16" height="1" rx="1" />
          </svg>
        </button>
        <button class="control-btn maximize-btn" @click="toggleMaximize">
          <svg v-if="!isMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4h16v16H4z" stroke-linejoin="round" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M10 5h9v9h-9zM5 10h9v9H5z" stroke-linejoin="round" />
          </svg>
        </button>
        <button class="control-btn close-btn" @click="close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M5 5l14 14M19 5l-14 14" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
    </div>
    <div class="main-container">
      <Sidebar class="sidebar" :has-new-log-error="hasNewLogError" @navigate="handleNavigate" />
      <main class="content">
        <div class="view-container">
          <div v-if="currentView === 'hidden'" class="hidden-view"></div>
          <Filelist
            v-else-if="currentView === 'keymouse'"
            :initialSubView="keymouseSubView.view"
            :initialFileName="keymouseSubView.fileName"
            :initialContent="keymouseSubView.content"
            @updateSubView="keymouseSubView.view = $event"
            @updateFileName="keymouseSubView.fileName = $event"
            @updateContent="keymouseSubView.content = $event"
          />
          <Screencast v-else-if="currentView === 'screencast'" />
          <Settings v-else-if="currentView === 'settings'" />
          <Logeditor
            v-else-if="currentView === 'logs'"
          />
        </div>
      </main>
    </div>
  </div>
</template>
