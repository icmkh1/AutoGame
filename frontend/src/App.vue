<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import Sidebar from './components/Sidebar.vue'
import KeymouseControl from './components/KeymouseControl.vue'
import './App.css'

type Theme = 'light' | 'dark'

const currentView = ref('hidden')
const isMaximized = ref(false)
const currentTheme = ref<Theme>('dark')
const minimizeToTray = ref(true)
const macroSwitch = ref('F1')
const isListening = ref(false)
const macroSwitchInput = ref<HTMLInputElement | null>(null)
let listenInterval: ReturnType<typeof setInterval> | null = null

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
    if (config.minimizeToTray !== undefined) {
      minimizeToTray.value = config.minimizeToTray
    }
    if (config.macroSwitch !== undefined) {
      macroSwitch.value = config.macroSwitch
    }
  } catch (e) {
    console.error('Failed to load config:', e)
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

async function saveMinimizeToTray(value: boolean) {
  try {
    const config = await (window as any).pywebview.api.get_config_file()
    config.minimizeToTray = value
    await (window as any).pywebview.api.save_config_file(config)
  } catch (e) {
    console.error('Failed to save config:', e)
  }
}

async function saveMacroSwitch(value: string) {
  try {
    const config = await (window as any).pywebview.api.get_config_file()
    config.macroSwitch = value
    await (window as any).pywebview.api.save_config_file(config)
  } catch (e) {
    console.error('Failed to save macroSwitch:', e)
  }
}

async function startListening() {
  if (listenInterval) return
  isListening.value = true
  listenInterval = setInterval(async () => {
    try {
      const keyName = await (window as any).pywebview.api.get_key_name()
      if (keyName) {
        if (keyName !== macroSwitch.value) {
          macroSwitch.value = keyName;
          saveMacroSwitch(keyName);
        }
        stopListening();
      }
    } catch (e) {
      // ignore errors during listening
    }
  }, 100)
}

function stopListening() {
  if (listenInterval) {
    clearInterval(listenInterval)
    listenInterval = null
  }
  isListening.value = false
  if (macroSwitchInput.value) {
    macroSwitchInput.value.blur()
  }
}

function onMacroSwitchFocus() {
  startListening()
}

function onMacroSwitchBlur() {
}

function onMacroSwitchInput(event: Event) {
  const target = event.target as HTMLInputElement
  target.value = macroSwitch.value
}


function handleNavigate(id: string) {
  currentView.value = id
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
})

provide('theme', currentTheme)
provide('themeColors', themeColors)
provide('toggleTheme', toggleTheme)
</script>

<template>
  <div class="app-container" :data-theme="currentTheme">
    <div class="title-bar pywebview-drag-region">
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
      <Sidebar class="sidebar" @navigate="handleNavigate" />
      <main class="content">
        <div class="view-container">
          <div v-if="currentView === 'hidden'" class="hidden-view"></div>
          <KeymouseControl v-else-if="currentView === 'keymouse'" />
          <h1 v-else-if="currentView === 'screencast'">手机投屏</h1>
          <div v-else-if="currentView === 'settings'" class="settings-view">
            <h1 class="section-title">设置</h1>
            <div class="scroll-container">
              <div class="settings-content">
                <div class="setting-item">
                  <span class="setting-label">主题模式</span>
                  <button class="theme-toggle-btn" @click="toggleTheme">
                    <svg v-if="currentTheme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="5"/>
                      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                    </svg>
                    <span>{{ currentTheme === 'dark' ? '明亮模式' : '暗黑模式' }}</span>
                  </button>
                </div>
                <div class="setting-item">
                  <span class="setting-label">关闭主界面</span>
                  <div class="radio-group">
                    <label class="radio-option" :class="{ active: minimizeToTray }">
                      <input type="radio" name="closeAction" :checked="minimizeToTray" @change="minimizeToTray = true; saveMinimizeToTray(true)" />
                      <span>最小化到托盘</span>
                    </label>
                    <label class="radio-option" :class="{ active: !minimizeToTray }">
                      <input type="radio" name="closeAction" :checked="!minimizeToTray" @change="minimizeToTray = false; saveMinimizeToTray(false)" />
                      <span>退出程序</span>
                    </label>
                  </div>
                </div>
                <div class="setting-item">
                  <span class="setting-label">宏开关</span>
                  <input
                    ref="macroSwitchInput"
                    type="text"
                    class="macro-switch-input"
                    v-model="macroSwitch"
                    @focus="onMacroSwitchFocus"
                    @blur="onMacroSwitchBlur"
                    @input.prevent="onMacroSwitchInput"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
