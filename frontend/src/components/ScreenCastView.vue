<template>
  <div class="screencast-viewer" :class="{ 'fullscreen-mode': isFullscreen }" :data-theme="currentTheme" @keydown="handleKeydown">
    <div v-if="!isFullscreen" class="viewer-sidebar">
      <button class="stop-btn" @click="handleStop">
        <span>停止</span>
      </button>
    </div>
    <div ref="viewport" class="viewport">
      <div class="screen-wrapper" :style="screenStyle">
        <canvas
          ref="canvas"
          @pointerdown.prevent="onPointer(0, $event)"
          @pointermove.prevent="onPointer(2, $event)"
          @pointerup.prevent="onPointer(1, $event)"
          @pointercancel.prevent="onPointer(1, $event)"
        />
        <div class="fps-overlay" v-if="showFps">{{ fps }}</div>
        <div v-if="!session.width" class="placeholder">
          <div class="spinner"></div>
          <p>{{ statusText }}</p>
        </div>
      </div>
    </div>
    <div v-if="!isFullscreen" class="viewer-sidebar viewer-sidebar-right">
      <div class="sidebar-top">
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="scrcpyExpandScreen"
            @mouseenter="showTooltip('scrcpy-expand-screen', '键位映射')"
            @mouseleave="hideTooltip('scrcpy-expand-screen')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="4" width="20" height="16" rx="2" ry="2"/>
              <line x1="7" y1="10" x2="10" y2="10"/>
              <line x1="14" y1="10" x2="17" y2="10"/>
              <line x1="4" y1="15" x2="7" y2="15"/>
              <line x1="10" y1="15" x2="14" y2="15"/>
              <line x1="17" y1="15" x2="20" y2="15"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-expand-screen']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-expand-screen'] }}
            </div>
          </Transition>
        </div>
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="scrcpyVolumeUp"
            @mouseenter="showTooltip('scrcpy-vol-up', '音量+')"
            @mouseleave="hideTooltip('scrcpy-vol-up')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <line x1="14" y1="12" x2="24" y2="12"/>
              <line x1="19" y1="7" x2="19" y2="17"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-vol-up']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-vol-up'] }}
            </div>
          </Transition>
        </div>
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="scrcpyVolumeDown"
            @mouseenter="showTooltip('scrcpy-vol-down', '音量-')"
            @mouseleave="hideTooltip('scrcpy-vol-down')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <line x1="14" y1="12" x2="24" y2="12"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-vol-down']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-vol-down'] }}
            </div>
          </Transition>
        </div>
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="toggleScrcpyFullscreen"
            @mouseenter="showTooltip('scrcpy-fullscreen', isFullscreen ? '退出全屏' : '全屏')"
            @mouseleave="hideTooltip('scrcpy-fullscreen')"
          >
            <svg v-if="!isFullscreen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 3 21 3 21 9"/>
              <polyline points="9 21 3 21 3 15"/>
              <line x1="21" y1="3" x2="14" y2="10"/>
              <line x1="3" y1="21" x2="10" y2="14"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 9 3 9 3 3"/>
              <polyline points="15 15 21 15 21 21"/>
              <line x1="3" y1="9" x2="10" y2="2"/>
              <line x1="21" y1="15" x2="14" y2="22"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-fullscreen']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-fullscreen'] }}
            </div>
          </Transition>
        </div>
        <div class="btn-wrapper">
          <button
            class="action-btn"
            :class="{ active: showFps }"
            @click="toggleShowFps"
            @mouseenter="hoveredButtons['toggle-fps'] = showFps ? '隐藏帧率' : '显示帧率'"
            @mouseleave="hideTooltip('toggle-fps')"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/>
              <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['toggle-fps']" class="tooltip tooltip-left">
              {{ hoveredButtons['toggle-fps'] }}
            </div>
          </Transition>
        </div>
      </div>
      <div class="sidebar-bottom">
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="scrcpyBack"
            @mouseenter="showTooltip('scrcpy-back', '返回')"
            @mouseleave="hideTooltip('scrcpy-back')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-back']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-back'] }}
            </div>
          </Transition>
        </div>
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="scrcpySwitchApp"
            @mouseenter="showTooltip('scrcpy-switch-app', '多应用')"
            @mouseleave="hideTooltip('scrcpy-switch-app')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/>
              <rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/>
              <rect x="3" y="14" width="7" height="7"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-switch-app']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-switch-app'] }}
            </div>
          </Transition>
        </div>
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="scrcpyHome"
            @mouseenter="showTooltip('scrcpy-home', '主页')"
            @mouseleave="hideTooltip('scrcpy-home')"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </button>
          <Transition name="tooltip">
            <div v-if="hoveredButtons['scrcpy-home']" class="tooltip tooltip-left">
              {{ hoveredButtons['scrcpy-home'] }}
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted, onBeforeUnmount, nextTick, type Ref } from "vue"
import "./ScreenCastView.css"

type Theme = "light" | "dark"

const currentTheme = inject<Ref<Theme>>("theme")

const props = defineProps<{
  connectionMode: "usb" | "wireless"
}>()

const emit = defineEmits<{
  (e: "back"): void
  (e: "fullscreen-change", isFull: boolean): void
}>()

// ------------------------------------------------------------------ #
// Screen / canvas state
// ------------------------------------------------------------------ #

const canvas = ref<HTMLCanvasElement | null>(null)
const viewport = ref<HTMLElement | null>(null)
const viewportSize = ref({ width: 0, height: 0 })
const session = ref({ width: 0, height: 0 })
const fps = ref(0)
const showFps = ref(true)
const statusText = ref("Connecting...")
const status = ref<{ running: boolean; deviceName?: string | null; error?: string | null }>({
  running: false,
})

const hoveredButtons = ref<Record<string, string>>({})
const isFullscreen = ref(false)

// ------------------------------------------------------------------ #
// Computed
// ------------------------------------------------------------------ #

const screenStyle = computed(() => {
  if (!session.value.width || !session.value.height) return {}
  const padding = 0
  const aw = Math.max(1, viewportSize.value.width - padding)
  const ah = Math.max(1, viewportSize.value.height - padding)
  const scale = Math.min(aw / session.value.width, ah / session.value.height)
  return {
    width: `${Math.floor(session.value.width * scale)}px`,
    height: `${Math.floor(session.value.height * scale)}px`,
  }
})

// ------------------------------------------------------------------ #
// Tooltip helpers
// ------------------------------------------------------------------ #

function showTooltip(key: string, text: string) {
  hoveredButtons.value[key] = text
}

function hideTooltip(key: string) {
  delete hoveredButtons.value[key]
}

// ------------------------------------------------------------------ #
// Control helpers
// ------------------------------------------------------------------ #

function scrcpyExpandScreen() {
  callApi("scrcpy_expand_screen").catch(() => {})
}

function scrcpyVolumeUp() {
  callApi("scrcpy_volume_up").catch(() => {})
}

function scrcpyVolumeDown() {
  callApi("scrcpy_volume_down").catch(() => {})
}

function toggleScrcpyFullscreen() {
  isFullscreen.value = !isFullscreen.value
  emit('fullscreen-change', isFullscreen.value)

  // 调用 pywebview 的窗口最大化/还原功能
  if ((window as any).pywebview && (window as any).pywebview.api) {
    (window as any).pywebview.api.toggle_maximize()
  }
}

async function toggleShowFps() {
  const newShowFps = !showFps.value

  delete hoveredButtons.value['toggle-fps']
  showFps.value = newShowFps

  await nextTick()
  hoveredButtons.value['toggle-fps'] = newShowFps ? '隐藏帧率' : '显示帧率'

  if (!(window as any).pywebview?.api) {
    console.warn('pywebview API not available')
    return
  }

  try {
    const config = await callApi("get_config_file")
    if (!config.screencast) config.screencast = {}
    config.screencast.showFps = newShowFps
    await callApi("save_config_file", config)
  } catch (e) {
    if (e instanceof Error && e.message.includes('ObjectDisposedException')) {
      console.warn('Window is closing, skipping save')
    } else {
      console.error('Failed to save showFps config:', e)
    }
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isFullscreen.value) {
    toggleScrcpyFullscreen()
  }
}

function scrcpyBack() {
  callApi("scrcpy_back").catch(() => {})
}

function scrcpySwitchApp() {
  callApi("scrcpy_switch_app").catch(() => {})
}

function scrcpyHome() {
  callApi("scrcpy_home").catch(() => {})
}

async function handleStop() {
  await stopConnection()
  emit("back")
}

// ------------------------------------------------------------------ #
// Video decoder state
// ------------------------------------------------------------------ #

let videoDecoder: VideoDecoder | null = null
let audioContext: AudioContext | null = null
let audioStartTime = 0
let videoConfigured = false
let pollTimer = 0
let fpsTimer = 0
let framesThisSecond = 0
let resizeObserver: ResizeObserver | null = null

// ------------------------------------------------------------------ #
// API helpers
// ------------------------------------------------------------------ #

function ensureApi() {
  if (!(window as any).pywebview?.api) throw new Error("pywebview API is not available")
}

async function callApi(method: string, ...args: any[]): Promise<any> {
  ensureApi()
  return await (window as any).pywebview.api[method](...args)
}

function base64ToBytes(payload: string) {
  const raw = atob(payload)
  const bytes = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i)
  return bytes
}

// ------------------------------------------------------------------ #
// Connection
// ------------------------------------------------------------------ #

async function startConnection() {
  try {
    statusText.value = "Connecting..."
    const config = await callApi("get_config_file")
    const scConfig = config.screencast || {}
    if (scConfig.showFps !== undefined) showFps.value = scConfig.showFps

    let resolvedSerial: string | undefined

    if (props.connectionMode === "wireless") {
      statusText.value = "Switching to wireless..."
      const result = await callApi("scrcpy_switch_to_wireless")
      if (result.ok) {
        resolvedSerial = result.serial
      } else {
        status.value = { running: false, error: result.error }
        statusText.value = result.error || "Wireless switch failed"
        return
      }
    } else {
      // USB mode - auto-discover or use serial
      const serial = await callApi("scrcpy_discover_usb_serial")
      resolvedSerial = serial || undefined
    }

    status.value = await callApi("scrcpy_start", resolvedSerial || null, scConfig)
    if (status.value.running) {
      statusText.value = `Connected to ${status.value.deviceName || "device"}`
      startPolling()
    } else {
      statusText.value = status.value.error || "Connection failed"
    }
  } catch (e) {
    statusText.value = e instanceof Error ? e.message : String(e)
  }
}

async function stopConnection() {
  stopPolling()
  closeDecoders()
  try {
    await callApi("scrcpy_stop")
  } catch {
    // ignore
  }
  status.value = { running: false }
}

// ------------------------------------------------------------------ #
// Polling
// ------------------------------------------------------------------ #

function startPolling() {
  stopPolling()
  pollTimer = window.setInterval(async () => {
    if (!status.value.running) return
    try {
      const events = await callApi("scrcpy_poll_events", 40)
      for (const event of events) handleEvent(event)
    } catch {
      // ignore
    }
  }, 24)
}

function stopPolling() {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = 0
  }
}

type StreamEvent = {
  kind: "session" | "video" | "audio" | "error"
  codec?: string | null
  width?: number
  height?: number
  pts?: number | null
  config?: boolean
  keyFrame?: boolean
  payload?: string
  message?: string
  clientResized?: boolean
}

function handleEvent(event: StreamEvent) {
  if (event.kind === "session") {
    session.value = { width: event.width || 0, height: event.height || 0 }
    resizeCanvas()
    return
  }
  if (event.kind === "video" && event.payload) {
    framesThisSecond++
    decodeVideo(event)
    return
  }
  if (event.kind === "audio" && event.payload) {
    playAudio(event.payload)
    return
  }
}

// ------------------------------------------------------------------ #
// Video decoding
// ------------------------------------------------------------------ #

function decodeVideo(event: StreamEvent) {
  if (!("VideoDecoder" in window)) return
  if (event.codec !== "h264") return

  const data = base64ToBytes(event.payload || "")

  if (!videoDecoder) {
    videoDecoder = new VideoDecoder({
      output(frame) {
        const cvs = canvas.value
        if (!cvs) {
          frame.close()
          return
        }
        const ctx = cvs.getContext("2d")
        if (ctx) {
          ctx.drawImage(frame, 0, 0, cvs.width, cvs.height)
        }
        frame.close()
      },
      error(e) {
        console.error("VideoDecoder error:", e.message)
      },
    })
  }

  if (!videoConfigured) {
    videoDecoder.configure({
      codec: "avc1.42E01E",
      optimizeForLatency: true,
      avc: { format: "annexb" },
    } as VideoDecoderConfig)
    videoConfigured = true
  }

  // Skip delta frames until a key frame arrives after configure
  if (!event.keyFrame && !videoConfigured) return

  const chunk = new EncodedVideoChunk({
    type: event.keyFrame ? "key" : "delta",
    timestamp: event.pts || performance.now() * 1000,
    data,
  })

  try {
    videoDecoder.decode(chunk)
  } catch (e) {
    console.error("Decode error:", e)
  }
}

function playAudio(payload: string) {
  const data = base64ToBytes(payload || "")
  if (!data.length) return

  if (!audioContext) {
    audioContext = new AudioContext({ sampleRate: 48000 })
    audioStartTime = audioContext.currentTime + 0.05
  }

  const frameCount = Math.floor(data.length / 4)
  if (frameCount <= 0) return

  const buffer = audioContext.createBuffer(2, frameCount, 48000)
  const ch0 = buffer.getChannelData(0)
  const ch1 = buffer.getChannelData(1)

  for (let i = 0; i < frameCount; i++) {
    const offset = i * 4
    ch0[i] = audioSample(data[offset], data[offset + 1])
    ch1[i] = audioSample(data[offset + 2], data[offset + 3])
  }

  const source = audioContext.createBufferSource()
  source.buffer = buffer
  source.connect(audioContext.destination)

  const scheduledTime = Math.max(audioContext.currentTime + 0.02, audioStartTime)
  source.start(scheduledTime)
  audioStartTime = scheduledTime + buffer.duration
}

function audioSample(lo: number, hi: number) {
  const val = (hi << 8) | lo
  return (val >= 32768 ? val - 65536 : val) / 32768
}

function closeDecoders() {
  if (videoDecoder) {
    videoDecoder.close()
    videoDecoder = null
  }
  videoConfigured = false
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
}

// ------------------------------------------------------------------ #
// Canvas / resize
// ------------------------------------------------------------------ #

function resizeCanvas() {
  const cvs = canvas.value
  if (!cvs || !session.value.width || !session.value.height) return
  cvs.width = session.value.width
  cvs.height = session.value.height
}

// ------------------------------------------------------------------ #
// Touch / pointer
// ------------------------------------------------------------------ #

async function onPointer(action: number, event: PointerEvent) {
  if (!status.value.running || !session.value.width || !session.value.height || !canvas.value) return

  const rect = canvas.value.getBoundingClientRect()
  const x = Math.max(0, Math.min(session.value.width, Math.round(((event.clientX - rect.left) / rect.width) * session.value.width)))
  const y = Math.max(0, Math.min(session.value.height, Math.round(((event.clientY - rect.top) / rect.height) * session.value.height)))

  if (action === 0) canvas.value.setPointerCapture(event.pointerId)
  if (action === 1) canvas.value.releasePointerCapture(event.pointerId)

  try {
    await callApi("scrcpy_send_touch", action, x, y, session.value.width, session.value.height)
  } catch {
    // ignore
  }
}

// ------------------------------------------------------------------ #
// Lifecycle
// ------------------------------------------------------------------ #

onMounted(async () => {
  fpsTimer = window.setInterval(() => {
    fps.value = framesThisSecond
    framesThisSecond = 0
  }, 1000)

  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (!entry) return
    viewportSize.value = {
      width: entry.contentRect.width,
      height: entry.contentRect.height,
    }
  })
  if (viewport.value) resizeObserver.observe(viewport.value)

  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeydown)

  await startConnection()
})

onBeforeUnmount(() => {
  if (fpsTimer) window.clearInterval(fpsTimer)
  resizeObserver?.disconnect()
  window.removeEventListener('keydown', handleKeydown)
  stopConnection()
})

// 暴露函数给父组件调用
defineExpose({
  toggleScrcpyFullscreen
})
</script>
