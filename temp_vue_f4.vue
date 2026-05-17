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
      <!-- Key Mapping Overlay -->
      <div v-if="showKeyMapping" class="key-mapping-overlay"
           :class="{ 'cursor-auto-hide': autoHideMouse && !altPressed }"
           @mousedown.left="onOverlayMouseDown"
           @mousemove="onOverlayMouseMove"
           @mouseup.left="onOverlayMouseUp"
           @click.right.prevent="onOverlayRightClick"
           @contextmenu.prevent
           ref="overlayRef">
        <div class="key-mapping-canvas" ref="kmCanvasRef" @mousedown.left.stop="onCanvasMouseDown($event)">
          <!-- Single controls -->
          <div v-for="ctrl in controls" :key="ctrl.id"
               class="key-control"
               :class="{ listening: editingControlId === ctrl.id }"
               :style="{ left: ctrl.x + 'px', top: ctrl.y + 'px', width: (ctrl.radius*2) + 'px', height: (ctrl.radius*2) + 'px' }"
               @mousedown.left.stop="startDrag($event, ctrl)">
            <div class="control-circle">
              <span class="control-label">{{ ctrl.label || (editingControlId === ctrl.id ? "..." : "?") }}</span>
              <button class="control-close" @click.stop="removeControl(ctrl.id)">&times;</button>
            </div>
          </div>
          <!-- DPad controls -->
          <div v-for="dpad in dpads" :key="dpad.id"
               class="key-control dpad"
               :style="{ left: dpad.x + 'px', top: dpad.y + 'px', width: dpad.size + 'px', height: dpad.size + 'px' }" @mousedown.left.stop="startDrag($event, dpad, 'dpad')">
            <div class="dpad-rect" :style="{ width: dpad.size + 'px', height: dpad.size + 'px' }"></div>
            <div class="dpad-circle" :style="{ width: dpad.size + 'px', height: dpad.size + 'px' }"></div>
            <div v-for="dir in ['up','down','left','right']" :key="dir"
                 class="dpad-key"
                 :class="{ listening: editingDpadId === dpad.id && editingDpadDir === dir }"
                 :style="getDpadKeyStyle(dpad, dir)"
                 @click.stop="editDpadKey(dpad, dir)">
              {{ dpad.keys[dir].label }}
            </div>
            <div class="resize-handle br" @mousedown.stop="startDpadResize($event, dpad)"></div>
            <div class="resize-handle tr" @mousedown.stop="startDpadResize($event, dpad)"></div>
            <div class="resize-handle bl" @mousedown.stop="startDpadResize($event, dpad)"></div>
            <div class="resize-handle tl" @mousedown.stop="startDpadResize($event, dpad)"></div>
            <button class="control-close" @click.stop="removeControl(dpad.id)" :style="{ position: 'absolute', top: '-6px', right: '-6px', zIndex: 10 }">&times;</button>
          </div>
          <!-- Swipe controls -->
          <div v-for="swp in swipes" :key="swp.id"
               class="key-control"
               :class="{ listening: editingControlId === swp.id }"
               :style="{ left: swp.x + 'px', top: swp.y + 'px', width: (swp.radius*2) + 'px', height: (swp.radius*2) + 'px' }"
               @mousedown.left.stop="startDrag($event, swp, 'swipe')">
            <div class="control-circle">
              <span class="control-label">{{ swp.label || "滑动" }}</span>
              <button class="control-close" @click.stop="removeControl(swp.id)">&times;</button>
            </div>
          </div>
          <!-- Swipe recording preview -->
          <svg v-if="isRecordingSwipe && swipePoints.length > 1" class="swipe-preview">
            <polyline :points="swipePoints.map(p => p.x + ',' + p.y).join(' ')"></polyline>
          </svg>
        </div>
        <!-- Sidebar -->
        <div class="key-mapping-sidebar">
          <div class="km-file-header">
            <span>键位文件</span>
            <button @click="createNewKeyMapping" title="新建">+</button>
          </div>
          <div class="km-files">
            <div v-for="f in keyMappingFiles" :key="f"
                 class="km-file-item"
                 :class="{ active: f === currentFile }"
                 @click="switchFile(f)">
              <template v-if="renamingFile === f">
                <input v-model="renameInput" @blur="doRename" @keyup.enter="doRename" ref="renameInputRef" />
              </template>
              <template v-else>
                <span class="km-file-name">{{ f }}</span>
                <div class="km-file-actions">
                  <button @click.stop="startRename(f)" title="重命名">&#9998;</button>
                  <button @click.stop="deleteFile(f)" title="删除">&times;</button>
                </div>
              </template>
            </div>
          </div>
          <div class="km-settings">
            <label class="km-toggle">
              <input type="checkbox" v-model="autoHideMouse" @change="onAutoHideChange" />
              <span>自动隐藏鼠标 (长按LAlt显示)</span>
            </label>
          </div>
          <div class="km-actions">
            <button class="km-btn close" @click="closeKeyMapping">关闭</button>
          </div>
        </div>
        <!-- Context menu -->
        <div v-if="contextMenu.show" class="context-menu"
             :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
          <div @click="createDirectionKey">方向键位(WASD)</div>
          <div @click="startSwipeRecording">滑动键位</div>
        </div>
      </div>
    </div>
    <div v-if="!isFullscreen" class="viewer-sidebar viewer-sidebar-right">
      <div class="sidebar-top">
        <div class="btn-wrapper">
          <button
            class="action-btn"
            @click="toggleKeyMapping"
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
const isKeyMappingActive = ref(false)

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
  // Key mapping execution during casting
  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
    const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
    // Find the control mapped to this key and send touch at its position
    execKeyDown(key)
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
  await teardownKeyCapture()

  stopConnection()
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



// ------------------------------------------------------------------ #
// Key Mapping State
// ------------------------------------------------------------------ #

const showKeyMapping = ref(false)
const keyMappingFiles = ref<string[]>([])
const currentFile = ref("")
const controls = ref<any[]>([])
const dpads = ref<any[]>([])
const swipes = ref<any[]>([])
const autoHideMouse = ref(false)
const altPressed = ref(false)
const contextMenu = ref({ show: false, x: 0, y: 0 })
const editingControlId = ref<string | null>(null)
const editingDpadId = ref<string | null>(null)
const editingDpadDir = ref<string | null>(null)
const isRecordingSwipe = ref(false)
const pendingSwipe = ref(false)
const swipePoints = ref<{x:number,y:number,delayMs:number}[]>([])
const swipeStartTime = ref(0)
const renamingFile = ref<string | null>(null)
const renameInput = ref("")
const renameInputRef = ref<HTMLInputElement | null>(null)
const overlayRef = ref<HTMLElement | null>(null)
const kmCanvasRef = ref<HTMLElement | null>(null)
let dragTarget: any = null
let dragType = ""
let dragOffsetX = 0
let dragOffsetY = 0
let resizeTarget: any = null
let resizeStartSize = 0
let resizeStartMouse = { x: 0, y: 0 }

// Available key names (from constants + button_mapping)
const KNOWN_KEYS = [
  "0","1","2","3","4","5","6","7","8","9",
  "A","B","C","D","E","F","G","H","I","J","K","L","M",
  "N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
  "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
  "Esc","Tab","CapsLock","LShift","RShift","LCtrl","RCtrl","LAlt","RAlt",
  "LWin","RWin","Back","Enter","Menu","Space",
  "Left","Up","Right","Down","Insert","Delete","Home","End","PgUp","PgDown",
  "Prtsc","ScrollLock","Pause",
  "Numpad0","Numpad1","Numpad2","Numpad3","Numpad4","Numpad5","Numpad6","Numpad7","Numpad8","Numpad9",
  "Add","Subtract","Multiply","Divide","Numlock","Decimal",
  "MLeft","MRight","Middle","MSide1","MSide2",
]

// Key name translation for display
const KEY_LABELS: Record<string, string> = {
  "MLeft": "左键", "MRight": "右键", "Middle": "中键",
  "MSide1": "侧键1", "MSide2": "侧键2",
  "Space": "空格", "Enter": "回车", "Back": "退格",
  "LShift": "左Shift", "RShift": "右Shift",
  "LCtrl": "左Ctrl", "RCtrl": "右Ctrl",
  "LAlt": "左Alt", "RAlt": "右Alt",
  "LWin": "左Win", "RWin": "右Win",
}

function controlId(prefix: string): string {
  return prefix + "_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6)
}

function normalizeKeyName(raw: string): string {
  // Map raw keyboard event key names to our known key names
  const map: Record<string, string> = {
    "Control": "LCtrl", "Shift": "LShift", "Alt": "LAlt", "Meta": "LWin",
    " ": "Space", "ArrowLeft": "Left", "ArrowRight": "Right", "ArrowUp": "Up", "ArrowDown": "Down",
  }
  return map[raw] || raw.toUpperCase()
}

function formatKeyName(key: string): string {
  return KEY_LABELS[key] || key
}

// ---- Overlay toggle ----
function toggleKeyMapping() {
  showKeyMapping.value = !showKeyMapping.value
  if (showKeyMapping.value) {
    loadKeyMappingFiles()
    setupKeyCapture()
  } else {
    closeKeyMapping()
  }
}

// ---- File management ----
async function loadKeyMappingFiles() {
  try {
    keyMappingFiles.value = await callApi("get_key_mapping_files")
    if (keyMappingFiles.value.length > 0 && !currentFile.value) {
      await switchFile(keyMappingFiles.value[0])
    }
  } catch (e) {
    console.error("Failed to load key mapping files:", e)
  }
}

async function switchFile(name: string) {
  if (renamingFile.value) return
  // Save current first
  await saveCurrentMapping()
  currentFile.value = name
  try {
    const data = await callApi("load_key_mapping_file", name)
    if (data) {
      controls.value = (data.controls || []).map((c: any) => ({ ...c }))
      dpads.value = (data.dpad || []).map((d: any) => ({ ...d }))
      swipes.value = (data.swipes || []).map((s: any) => ({ ...s }))
      autoHideMouse.value = data.autoHideMouse || false
    }
  } catch (e) {
    console.error("Failed to load key mapping:", e)
  }
}

async function saveCurrentMapping() {
  if (!currentFile.value) return
  const data = {
    version: 1,
    name: currentFile.value,
    autoHideMouse: autoHideMouse.value,
    controls: controls.value.map(c => ({ id: c.id, type: "single", key: c.key, label: c.label, x: c.x, y: c.y, radius: c.radius })),
    dpad: dpads.value.map(d => ({ id: d.id, type: "dpad", x: d.x, y: d.y, size: d.size, keys: d.keys })),
    swipes: swipes.value.map(s => ({ id: s.id, type: "swipe", label: s.label, key: s.key || "", x: s.x, y: s.y, radius: s.radius, path: s.path })),
  }
  try {
    await callApi("save_key_mapping_file", currentFile.value, data)
    await callApi("apply_key_mapping", currentFile.value)
    isKeyMappingActive.value = true
  } catch (e) {
    console.error("Failed to save key mapping:", e)
  }
}

async function createNewKeyMapping() {
  try {
    const name = await callApi("create_key_mapping_file")
    if (name) {
      keyMappingFiles.value.push(name)
      await switchFile(name)
    }
  } catch (e) {
    console.error("Failed to create key mapping:", e)
  }
}

function startRename(name: string) {
  renamingFile.value = name
  renameInput.value = name
  nextTick(() => renameInputRef.value?.focus())
}

async function doRename() {
  if (!renamingFile.value || !renameInput.value.trim()) {
    renamingFile.value = null
    return
  }
  const oldName = renamingFile.value
  const newName = renameInput.value.trim()
  renamingFile.value = null
  if (oldName === newName) return
  try {
    await callApi("rename_key_mapping_file", oldName, newName)
    const idx = keyMappingFiles.value.indexOf(oldName)
    if (idx >= 0) keyMappingFiles.value[idx] = newName
    if (currentFile.value === oldName) currentFile.value = newName
  } catch (e) {
    console.error("Failed to rename:", e)
  }
}

async function deleteFile(name: string) {
  try {
    await callApi("delete_key_mapping_file", name)
    keyMappingFiles.value = keyMappingFiles.value.filter(f => f !== name)
    if (currentFile.value === name) {
      currentFile.value = keyMappingFiles.value[0] || ""
      if (currentFile.value) await switchFile(currentFile.value)
    }
  } catch (e) {
    console.error("Failed to delete:", e)
  }
}

// ---- Canvas interactions ----
function onCanvasMouseDown(e: MouseEvent) {
  if (!kmCanvasRef.value) return
  contextMenu.value.show = false
  if (pendingSwipe.value) {
    pendingSwipe.value = false
    isRecordingSwipe.value = true
    swipePoints.value = []
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    swipePoints.value = [{ x, y, delayMs: 0 }]
    swipeStartTime.value = Date.now()
    return
  }
  if (isRecordingSwipe.value) return
  const rect = kmCanvasRef.value.getBoundingClientRect()
  const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
  const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)

  const ctrl = {
    id: controlId("ctrl"),
    key: "",
    label: "",
    x, y,
    radius: 25,
  }
  controls.value.push(ctrl)
  editingControlId.value = ctrl.id
}

function onOverlayRightClick(e: MouseEvent) {
  contextMenu.value = { show: true, x: e.clientX, y: e.clientY }
}

function createDirectionKey() {
  contextMenu.value.show = false
  if (!kmCanvasRef.value) return
  const rect = kmCanvasRef.value.getBoundingClientRect()
  const cx = Math.round(contextMenu.value.x - rect.left + kmCanvasRef.value.scrollLeft)
  const cy = Math.round(contextMenu.value.y - rect.top + kmCanvasRef.value.scrollTop)
  const dpad = {
    id: controlId("dpad"),
    x: cx, y: cy,
    size: 120,
    keys: {
      up: { key: "W", label: "W" },
      down: { key: "S", label: "S" },
      left: { key: "A", label: "A" },
      right: { key: "D", label: "D" },
    }
  }
  dpads.value.push(dpad)
  autoSave()
}

function startSwipeRecording() {
  contextMenu.value.show = false
  pendingSwipe.value = true
}

function onOverlayMouseDown(e: MouseEvent) {
  if (pendingSwipe.value && kmCanvasRef.value) {
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    swipePoints.value = [{ x, y, delayMs: 0 }]
    swipeStartTime.value = Date.now()
  }
}

function onOverlayMouseMove(e: MouseEvent) {
  if (isRecordingSwipe.value && swipeStartTime.value > 0 && kmCanvasRef.value) {
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    const delay = Date.now() - swipeStartTime.value
    const last = swipePoints.value[swipePoints.value.length - 1]
    // Throttle: only record if moved > 5px or 30ms passed
    if (!last || Math.hypot(x - last.x, y - last.y) > 5 || delay - (last.delayMs || 0) > 30) {
      swipePoints.value.push({ x, y, delayMs: delay })
    }
  }

  // Drag handling
  if (dragTarget) {
    if (!kmCanvasRef.value) return
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const newX = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft - dragOffsetX)
    const newY = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop - dragOffsetY)
    dragTarget.x = Math.max(0, newX)
    dragTarget.y = Math.max(0, newY)
  }

  // DPad resize
  if (resizeTarget && kmCanvasRef.value) {
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const mx = e.clientX - rect.left + kmCanvasRef.value.scrollLeft
    const my = e.clientY - rect.top + kmCanvasRef.value.scrollTop
    const dx = mx - resizeTarget.x
    const dy = my - resizeTarget.y
    const newSize = Math.max(60, Math.round(Math.hypot(dx, dy) * 2))
    if (newSize !== resizeTarget.size) {
      resizeTarget.size = newSize
    }
  }
}

function onOverlayMouseUp(e: MouseEvent) {
  if (isRecordingSwipe.value && swipePoints.value.length > 0 && kmCanvasRef.value) {
    isRecordingSwipe.value = false
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const ex = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const ey = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    // Add last point
    const lastDelay = Date.now() - swipeStartTime.value
    const lastPt = swipePoints.value[swipePoints.value.length - 1]
    if (!lastPt || lastPt.x !== ex || lastPt.y !== ey) {
      swipePoints.value.push({ x: ex, y: ey, delayMs: lastDelay })
    }
    const swp = {
      id: controlId("swp"),
      label: "滑动" + (swipes.value.length + 1),
      key: "",
      x: ex, y: ey,
      radius: 25,
      path: swipePoints.value.map(p => ({ ...p })),
    }
    swipes.value.push(swp)
    swipePoints.value = []
    swipeStartTime.value = 0
    autoSave()
  }

  if (dragTarget) {
    dragTarget = null
    autoSave()
  }
  if (resizeTarget) {
    resizeTarget = null
    autoSave()
  }
}

function startDrag(e: MouseEvent, ctrl: any, type = "single") {
  if (!kmCanvasRef.value) return
  const rect = kmCanvasRef.value.getBoundingClientRect()
  dragTarget = ctrl
  dragType = type
  dragOffsetX = e.clientX - rect.left + kmCanvasRef.value.scrollLeft - ctrl.x
  dragOffsetY = e.clientY - rect.top + kmCanvasRef.value.scrollTop - ctrl.y
}

function startDpadResize(e: MouseEvent, dpad: any) {
  resizeTarget = dpad
  resizeStartSize = dpad.size
  resizeStartMouse = { x: e.clientX, y: e.clientY }
}

function editDpadKey(dpad: any, dir: string) {
  if (editingControlId.value) return
  editingDpadId.value = dpad.id
  editingDpadDir.value = dir
}

function removeControl(id: string) {
  controls.value = controls.value.filter(c => c.id !== id)
  dpads.value = dpads.value.filter(d => d.id !== id)
  swipes.value = swipes.value.filter(s => s.id !== id)
  autoSave()
}

// ---- DPad key position calculation ----
function getDpadKeyStyle(dpad: any, dir: string) {
  const r = dpad.size / 2
  const dist = r * 0.55
  const angles: Record<string, number> = { up: -90, down: 90, left: 180, right: 0 }
  const rad = (angles[dir] * Math.PI) / 180
  const kx = r + Math.cos(rad) * dist
  const ky = r + Math.sin(rad) * dist
  return {
    left: kx + 'px',
    top: ky + 'px',
    transform: 'translate(-50%, -50%)',
  }
}

// ---- Auto-save ----
let autoSaveTimer = 0
function autoSave() {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = window.setTimeout(() => {
    saveCurrentMapping()
  }, 500)
}

// ---- Key capture ----
let keyCaptureHandler: ((e: KeyboardEvent) => void) | null = null

function setupKeyCapture() {
  if (keyCaptureHandler) return
  keyCaptureHandler = (e: KeyboardEvent) => {
    if (editingControlId.value) {
      e.preventDefault()
      e.stopPropagation()
      const ctrl = controls.value.find(c => c.id === editingControlId.value)
      if (ctrl) {
        const raw = e.key === " " ? "Space" : normalizeKeyName(e.key)
        if (KNOWN_KEYS.includes(raw)) {
          // Check duplicate
          const dup = [...controls.value, ...swipes.value].find(
            c => c.id !== ctrl.id && c.key === raw
          )
          if (dup) {
            return  // Silently reject duplicates
          }
          ctrl.key = raw
          ctrl.label = formatKeyName(raw)
        } else {
          // Try to use raw key as label
          ctrl.key = raw
          ctrl.label = raw
        }
        editingControlId.value = null
        autoSave()
      }
    }
    if (editingDpadId.value && editingDpadDir.value) {
      e.preventDefault()
      e.stopPropagation()
      const dpad = dpads.value.find(d => d.id === editingDpadId.value)
      if (dpad) {
        const raw = e.key === " " ? "Space" : normalizeKeyName(e.key)
        if (KNOWN_KEYS.includes(raw)) {
          dpad.keys[editingDpadDir.value] = { key: raw, label: formatKeyName(raw) }
        } else {
          dpad.keys[editingDpadDir.value] = { key: raw, label: raw }
        }
        editingDpadId.value = null
        editingDpadDir.value = null
        autoSave()
      }
    }
  }
  document.addEventListener("keydown", keyCaptureHandler, true)
}

function teardownKeyCapture() {
  if (keyCaptureHandler) {
    document.removeEventListener("keydown", keyCaptureHandler, true)
    keyCaptureHandler = null
  }
}

// ---- Mouse button capture (for left click creating controls, we need separate handling) ----
// This is handled via pointerdown detection on the overlay

// ---- Auto-hide mouse ----
function onAutoHideChange() {
  autoSave()
}

// Listen for custom events from backend hook
function setupAutoHideEvents() {
  window.addEventListener("km-show-cursor", () => { altPressed.value = true })
  window.addEventListener("km-hide-cursor", () => { altPressed.value = false })
}

// ---- Close overlay ----
async function closeKeyMapping() {
  await saveCurrentMapping()
  editingControlId.value = null
  editingDpadId.value = null
  editingDpadDir.value = null
  contextMenu.value.show = false
  isRecordingSwipe.value = false
  pendingSwipe.value = false
  swipePoints.value = []
  teardownKeyCapture()
  showKeyMapping.value = false
  // Activate auto-hide mouse if enabled
  if (autoHideMouse.value) {
    callApi("set_key_mapping_auto_hide", true).catch(() => {})
  }
  // Keep key mapping active for execution
  isKeyMappingActive.value = true
}

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
  window.addEventListener('keyup', handleKeyup)

  setupAutoHideEvents()

  await startConnection()
})

onBeforeUnmount(() => {
  if (fpsTimer) window.clearInterval(fpsTimer)
  resizeObserver?.disconnect()
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('keyup', handleKeyup)
  teardownKeyCapture()

  stopConnection()
})

function findControlByKey(key) {
  for (const ctrl of controls.value) {
    if (ctrl.key === key) return { ...ctrl, kind: "single" }
  }
  for (const swp of swipes.value) {
    if (swp.key === key) return { ...swp, kind: "swipe" }
  }
  for (const dpad of dpads.value) {
    for (const dir of ["up", "down", "left", "right"]) {
      if (dpad.keys[dir].key === key) return { ...dpad, kind: "dpad", dir: dir }
    }
  }
  return null
}

function execKeyDown(key) {
  const mapped = findControlByKey(key)
  if (!mapped || !session.value.width || !session.value.height) return
  const sw = session.value.width
  const sh = session.value.height
  if (mapped.kind === "single") {
    callApi("scrcpy_send_touch", 0, mapped.x, mapped.y, sw, sh).catch(() => {})
  } else if (mapped.kind === "dpad") {
    const dirOffsets = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }
    const [dx, dy] = dirOffsets[mapped.dir] || [0, 0]
    const dist = mapped.size * 0.4
    const ex = Math.round(mapped.x + dx * dist)
    const ey = Math.round(mapped.y + dy * dist)
    callApi("scrcpy_send_touch", 0, mapped.x, mapped.y, sw, sh).catch(() => {})
    callApi("scrcpy_send_touch", 2, ex, ey, sw, sh).catch(() => {})
    callApi("scrcpy_send_touch", 1, ex, ey, sw, sh).catch(() => {})
  } else if (mapped.kind === "swipe" && mapped.path && mapped.path.length > 1) {
    callApi("key_mapping_swipe", mapped.path).catch(() => {})
  }
}

function execKeyUp(key) {
  const mapped = findControlByKey(key)
  if (!mapped || !session.value.width || !session.value.height) return
  const sw = session.value.width
  const sh = session.value.height
  if (mapped.kind === "single") {
    callApi("scrcpy_send_touch", 1, mapped.x, mapped.y, sw, sh).catch(() => {})
  }
}

function handleKeyup(event) {
  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
    const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
    execKeyUp(key)
  }
}

// 暴露函数给父组件调用
defineExpose({
  toggleScrcpyFullscreen
})
</script>






