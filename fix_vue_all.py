with open("temp_vue_fix.vue", "r", encoding="utf-8") as f:
    content = f.read()

changes = 0

# Fix 1: DPad container dimensions + drag
old = '<div v-for="dpad in dpads" :key="dpad.id"\n               class="key-control dpad"\n               :style="{ left: dpad.x + chr(39) + "px" + chr(39) + \", top: dpad.y + chr(39) + "px" + chr(39) + \" }\">'

# Actually let me just do simple replacements
old1 = """               :style="{ left: dpad.x + 'px', top: dpad.y + 'px' }">"""
new1 = """               :style="{ left: dpad.x + 'px', top: dpad.y + 'px', width: dpad.size + 'px', height: dpad.size + 'px' }"
               @mousedown.left.stop="startDrag($event, dpad, 'dpad')">"""

# Find the dpad template by looking for the specific pattern
idx = content.find('<div v-for="dpad in dpads" :key="dpad.id"')
if idx >= 0:
    end_idx = content.find(">", idx)
    if end_idx >= 0:
        opener = content[idx:end_idx+1]
        new_opener = opener[:-1] + ', width: dpad.size + chr(39) + \"px\" + chr(39) + \", height: dpad.size + chr(39) + \"px\" + chr(39) + \" }\"\n               @mousedown.left.stop=\"startDrag($event, dpad, 'dpad')\">"
        content = content.replace(opener, new_opener)
        changes += 1
        print("Fix 1 applied: dpad dimensions + drag")
else:
    # Try direct text match
    target = """          <div v-for="dpad in dpads" :key="dpad.id"
               class="key-control dpad"
               :style="{ left: dpad.x + 'px', top: dpad.y + 'px' }">"""
    if target in content:
        replacement = """          <div v-for="dpad in dpads" :key="dpad.id"
               class="key-control dpad"
               :style="{ left: dpad.x + 'px', top: dpad.y + 'px', width: dpad.size + 'px', height: dpad.size + 'px' }"
               @mousedown.left.stop="startDrag($event, dpad, 'dpad')">"""
        content = content.replace(target, replacement)
        changes += 1
        print("Fix 1 applied: dpad dimensions + drag")
    else:
        print("Fix 1 WARNING: pattern not found")

# Fix 2: getDpadKeyStyle - relative coords
target2 = """  const kx = dpad.x + Math.cos(rad) * dist"""
if target2 in content:
    content = content.replace(target2, "  const kx = r + Math.cos(rad) * dist")
    target2b = """  const ky = dpad.y + Math.sin(rad) * dist"""
    content = content.replace(target2b, "  const ky = r + Math.sin(rad) * dist")
    changes += 1
    print("Fix 2 applied: getDpadKeyStyle relative coords")
else:
    print("Fix 2 WARNING: pattern getDpadKeyStyle not found")

# Fix 3: swipe recording needs pendingSwipe
# Add pendingSwipe ref
old3 = "const isRecordingSwipe = ref(false)\r\nconst swipePoints = ref<{x:number,y:number,delayMs:number}[]>([])"
new3 = "const isRecordingSwipe = ref(false)\r\nconst pendingSwipe = ref(false)\r\nconst swipePoints = ref<{x:number,y:number,delayMs:number}[]>([])"
content = content.replace(old3, new3)
changes += 1
print("Fix 3 applied: added pendingSwipe ref")

# Fix 4: startSwipeRecording sets pending flag
old4 = """function startSwipeRecording() {
  contextMenu.value.show = false
  isRecordingSwipe.value = true
  swipePoints.value = []
  swipeStartTime.value = Date.now()
}"""
new4 = """function startSwipeRecording() {
  contextMenu.value.show = false
  pendingSwipe.value = true
}"""
content = content.replace(old4, new4)
changes += 1
print("Fix 4 applied: startSwipeRecording sets pendingSwipe")

# Fix 5: onOverlayMouseDown - handle pendingSwipe"""
old5 = """function onOverlayMouseDown(e: MouseEvent) {
  if (isRecordingSwipe.value && kmCanvasRef.value) {
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    swipePoints.value = [{ x, y, delayMs: 0 }]
    swipeStartTime.value = Date.now()
  }
}"""
new5 = """function onOverlayMouseDown(e: MouseEvent) {
  if (pendingSwipe.value && kmCanvasRef.value) {
    pendingSwipe.value = false
    isRecordingSwipe.value = true
    swipePoints.value = []
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    swipePoints.value = [{ x, y, delayMs: 0 }]
    swipeStartTime.value = Date.now()
  }
}"""
content = content.replace(old5, new5)
changes += 1
print("Fix 5 applied: onOverlayMouseDown handles pendingSwipe")

# Fix 6: onCanvasLeftClick - skip during swipe
old6 = """  // Don't create controls while swipe recording is active
  if (isRecordingSwipe.value || pendingSwipe.value) return"""
# This was already added in the previous edit session, check if it exists
if "isRecordingSwipe.value || pendingSwipe.value" not in content:
    # Find the line after contextMenu hiding and before rect calculation
    target6 = """  contextMenu.value.show = false
  const rect = kmCanvasRef.value.getBoundingClientRect()"""
    if target6 in content:
        content = content.replace(target6, """  contextMenu.value.show = false
  if (isRecordingSwipe.value || pendingSwipe.value) return
  const rect = kmCanvasRef.value.getBoundingClientRect()""")
        changes += 1
        print("Fix 6 applied: onCanvasLeftClick skips during swipe")
    else:
        print("Fix 6 WARNING: onCanvasLeftClick guard not found")
else:
    print("Fix 6 skip: guard already exists")

# Fix 7: closeKeyMapping resets pendingSwipe
old7 = """  isRecordingSwipe.value = false
  swipePoints.value = []"""
new7 = """  isRecordingSwipe.value = false
  pendingSwipe.value = false
  swipePoints.value = []"""
if old7 in content:
    content = content.replace(old7, new7)
    changes += 1
    print("Fix 7 applied: closeKeyMapping resets pendingSwipe")

# Fix 8: .prevent on context menu items
old8 = """          <div @click="createDirectionKey">方向键位(WASD)</div>
          <div @click="startSwipeRecording">滑动键位</div>"""
new8 = """          <div @click.prevent="createDirectionKey">方向键位(WASD)</div>
          <div @click.prevent="startSwipeRecording">滑动键位</div>"""
if old8 in content:
    content = content.replace(old8, new8)
    changes += 1
    print("Fix 8 applied: .prevent on context menu")

# Fix 9: Fix createDirectionKey to use proper position
old9 = """function createDirectionKey() {
  contextMenu.value.show = false
  if (!kmCanvasRef.value) return
  const rect = kmCanvasRef.value.getBoundingClientRect()
  const cx = Math.round(contextMenu.value.x - rect.left + kmCanvasRef.value.scrollLeft)
  const cy = Math.round(contextMenu.value.y - rect.top + kmCanvasRef.value.scrollTop)"""
new9 = """function createDirectionKey() {
  contextMenu.value.show = false
  if (!kmCanvasRef.value || !overlayRef.value) return
  const rect = overlayRef.value.getBoundingClientRect()
  const cx = Math.round(contextMenu.value.x - rect.left)
  const cy = Math.round(contextMenu.value.y - rect.top)"""
if old9 in content:
    content = content.replace(old9, new9)
    changes += 1
    print("Fix 9 applied: createDirectionKey uses overlay coordinates")
else:
    print("Fix 9 WARNING: createDirectionKey not found")

print(f"\nTotal changes: {changes}")

with open("temp_vue_fix.vue", "w", encoding="utf-8") as f:
    f.write(content)
