import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_scv.vue", "r", encoding="utf-8") as f:
    content = f.read()

# Step 1: Replace the scrcpyExpandScreen button click handler
# Change: @click="scrcpyExpandScreen" -> @click="toggleKeyMapping"
content = content.replace(
    '@click="scrcpyExpandScreen"',
    '@click="toggleKeyMapping"'
)

# Step 2: After </div> closing .screen-wrapper, insert the overlay template
screen_wrapper_close = '''      </div>
    </div>
    <div v-if="!isFullscreen" class="viewer-sidebar viewer-sidebar-right">'''

overlay_template = '''      </div>
      <!-- Key Mapping Overlay -->
      <div v-if="showKeyMapping" class="key-mapping-overlay"
           :class="{ 'cursor-auto-hide': autoHideMouse && !altPressed }"
           @mousedown.left="onOverlayMouseDown"
           @mousemove="onOverlayMouseMove"
           @mouseup.left="onOverlayMouseUp"
           @click.right.prevent="onOverlayRightClick"
           @contextmenu.prevent
           ref="overlayRef">
        <div class="key-mapping-canvas" ref="kmCanvasRef" @mousedown.left.stop="onCanvasLeftClick">
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
               :style="{ left: dpad.x + 'px', top: dpad.y + 'px' }">
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
              <span class="control-label">{{ swp.label || "\u6ED1\u52A8" }}</span>
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
            <span>\u952E\u4F4D\u6587\u4EF6</span>
            <button @click="createNewKeyMapping" title="\u65B0\u5EFA">+</button>
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
                  <button @click.stop="startRename(f)" title="\u91CD\u547D\u540D">&#9998;</button>
                  <button @click.stop="deleteFile(f)" title="\u5220\u9664">&times;</button>
                </div>
              </template>
            </div>
          </div>
          <div class="km-settings">
            <label class="km-toggle">
              <input type="checkbox" v-model="autoHideMouse" @change="onAutoHideChange" />
              <span>\u81EA\u52A8\u9690\u85CF\u9F20\u6807 (\u957F\u6309LAlt\u663E\u793A)</span>
            </label>
          </div>
          <div class="km-actions">
            <button class="km-btn close" @click="closeKeyMapping">\u5173\u95ED</button>
          </div>
        </div>
        <!-- Context menu -->
        <div v-if="contextMenu.show" class="context-menu"
             :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }">
          <div @click="createDirectionKey">\u65B9\u5411\u952E\u4F4D(WASD)</div>
          <div @click="startSwipeRecording">\u6ED1\u52A8\u952E\u4F4D</div>
        </div>
      </div>
    </div>
    <div v-if="!isFullscreen" class="viewer-sidebar viewer-sidebar-right">'''

content = content.replace(screen_wrapper_close, overlay_template)

# Step 3: Add key mapping script after the imports/defines
# Find the script setup section and add the key mapping logic

# First, find where the script setup starts
script_start = '''import { ref, computed, inject, onMounted, onBeforeUnmount, nextTick, type Ref } from "vue"'''

# The script section needs an import for watch
content = content.replace(
    'import { ref, computed, inject, onMounted, onBeforeUnmount, nextTick, type Ref } from "vue"',
    'import { ref, computed, inject, onMounted, onBeforeUnmount, nextTick, watch, type Ref } from "vue"'
)

# Add key mapping state and functions before onMounted
km_state = '''

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
  "MLeft": "\u5DE6\u952E", "MRight": "\u53F3\u952E", "Middle": "\u4E2D\u952E",
  "MSide1": "\u4FA7\u952E1", "MSide2": "\u4FA7\u952E2",
  "Space": "\u7A7A\u683C", "Enter": "\u56DE\u8F66", "Back": "\u9000\u683C",
  "LShift": "\u5DE6Shift", "RShift": "\u53F3Shift",
  "LCtrl": "\u5DE6Ctrl", "RCtrl": "\u53F3Ctrl",
  "LAlt": "\u5DE6Alt", "RAlt": "\u53F3Alt",
  "LWin": "\u5DE6Win", "RWin": "\u53F3Win",
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
function onCanvasLeftClick(e: MouseEvent) {
  if (!overlayRef.value || !kmCanvasRef.value) return
  contextMenu.value.show = false
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
  isRecordingSwipe.value = true
  swipePoints.value = []
  swipeStartTime.value = Date.now()
}

function onOverlayMouseDown(e: MouseEvent) {
  if (isRecordingSwipe.value && kmCanvasRef.value) {
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
      label: "\u6ED1\u52A8" + (swipes.value.length + 1),
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
  const kx = dpad.x + Math.cos(rad) * dist
  const ky = dpad.y + Math.sin(rad) * dist
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
  if (autoHideMouse.value) {
    callApi("set_key_mapping_auto_hide", true).catch(() => {})
  } else {
    callApi("set_key_mapping_auto_hide", false).catch(() => {})
  }
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
  swipePoints.value = []
  teardownKeyCapture()
  showKeyMapping.value = false
  // Close key mapping on backend - remove active mapping when closing overlay
  try {
    await callApi("remove_key_mapping")
  } catch {}
}
'''

# Insert key mapping state before onMounted
on_mounted_marker = "onMounted(async () => {"
idx = content.find(on_mounted_marker)
if idx >= 0:
    content = content[:idx] + km_state + "\n" + content[idx:]

# Add setupAutoHideEvents to onMounted
content = content.replace(
    on_mounted_marker,
    on_mounted_marker
)

# Add auto-hide event setup in onMounted
content = content.replace(
    "await startConnection()",
    "setupAutoHideEvents()\r\n  await startConnection()"
)

# Add teardown in onBeforeUnmount
content = content.replace(
    "stopConnection()",
    "teardownKeyCapture()\r\n  stopConnection()"
)

# Add remove_key_mapping in stopConnection
content = content.replace(
    'async function stopConnection() {\r\n  stopPolling()\r\n  closeDecoders()',
    'async function stopConnection() {\r\n  try { await callApi("remove_key_mapping") } catch {}\r\n  stopPolling()\r\n  closeDecoders()'
)

# Export toggleKeyMapping in defineExpose
content = content.replace(
    'defineExpose({\r\n  toggleScrcpyFullscreen\r\n})',
    'defineExpose({\r\n  toggleScrcpyFullscreen,\r\n  toggleKeyMapping\r\n})'
)

with open("temp_scv.vue", "w", encoding="utf-8") as f:
    f.write(content)
print(f"OK: {len(content)}")
