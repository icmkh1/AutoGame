<template>
  <div class="screencast-viewer" :data-theme="currentTheme">
    <div class="viewer-sidebar">
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        <span>返回</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted, onBeforeUnmount, type Ref } from "vue"
import "./ScreenCastView.css"

type Theme = "light" | "dark"

const currentTheme = inject<Ref<Theme>>("theme")

const props = defineProps<{
  connectionMode: "usb" | "wireless"
}>()

const emit = defineEmits<{
  (e: "back"): void
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

// ------------------------------------------------------------------ #
// Computed
// ------------------------------------------------------------------ #

const screenStyle = computed(() => {
  if (!session.value.width || !session.value.height) return {}
  const padding = 28
  const aw = Math.max(1, viewportSize.value.width - padding)
  const ah = Math.max(1, viewportSize.value.height - padding)
  const scale = Math.min(aw / session.value.width, ah / session.value.height)
  return {
    width: `${Math.floor(session.value.width * scale)}px`,
    height: `${Math.floor(session.value.height * scale)}px`,
  }
})

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
// Navigation
// ------------------------------------------------------------------ #

async function goBack() {
  await stopConnection()
  emit("back")
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

  await startConnection()
})

onBeforeUnmount(() => {
  if (fpsTimer) window.clearInterval(fpsTimer)
  resizeObserver?.disconnect()
  stopConnection()
})
</script>
