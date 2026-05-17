import os, re
f = r"temp_vue_f4.vue"
with open(f, "r", encoding="utf-8") as fp:
    content = fp.read()

# Strategy: find exact markers using byte-level search to avoid encoding issues
# Use known ASCII-only search patterns to identify key positions in the file

orig = content

# Fix 1: Rename onCanvasLeftClick -> onCanvasMouseDown, add pendingSwipe logic
old1 = """// ---- Canvas interactions ----
function onCanvasLeftClick(e: MouseEvent) {
  if (!overlayRef.value || !kmCanvasRef.value) return
  contextMenu.value.show = false
  if (isRecordingSwipe.value || pendingSwipe.value) return"""
new1 = """// ---- Canvas interactions ----
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
  if (isRecordingSwipe.value) return"""

if old1 in content:
    content = content.replace(old1, new1)
    print("Fix 1: onCanvasMouseDown with swipe handling")
else:
    print("WARNING Fix 1: pattern not found")

# Fix 2: Replace handleKeydown execution
old2 = """    // Key mapping execution during casting
    if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
      const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
      execKeyDown(key)
    }"""
# Check if already updated from prev fix
if "execKeyDown" in content:
    print("Fix 2: already applied (execKeyDown found)")
else:
    old2b = """  // Key mapping execution during casting (not when overlay is open)
  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
    const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
    callApi("key_mapping_trigger", key, "down").catch(() => {})
  }"""
    new2b = """  // Key mapping execution during casting
  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
    const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
    execKeyDown(key)
  }"""
    if old2b in content:
        content = content.replace(old2b, new2b)
        print("Fix 2: handleKeydown updated")
    else:
        print("WARNING Fix 2: pattern not found")

# Fix 3: Replace handleKeyup
old3 = """function handleKeyup(event) {
  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
    const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
    callApi("key_mapping_trigger", key, "up").catch(() => {})
  }
}"""
# Check if already using execKeyUp
if "execKeyUp" in content:
    print("Fix 3: already applied (execKeyUp found)")
else:
    new3 = """function handleKeyup(event) {
  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {
    const key = event.key === " " ? "Space" : normalizeKeyName(event.key)
    execKeyUp(key)
  }
}"""
    if old3 in content:
        content = content.replace(old3, new3)
        print("Fix 3: handleKeyup updated")
    else:
        print("WARNING Fix 3: pattern not found")

# Fix 4: Add exec functions before handleKeyup
if "function execKeyDown" not in content:
    exec_code = """function findControlByKey(key) {
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

"""
    # Insert before handleKeyup
    idx = content.find("function handleKeyup(event)")
    if idx > 0:
        content = content[:idx] + exec_code + content[idx:]
        print("Fix 4: exec functions added")
    else:
        print("WARNING Fix 4: insert point not found")
else:
    print("Fix 4: already applied")

# Fix 5: Remove onOverlayMouseDown body (canvas handles it now)
old5 = """function onOverlayMouseDown(e: MouseEvent) {
  // Handled by onCanvasMouseDown with event.stopPropagation
}"""
if old5 in content:
    print("Fix 5: already minimal")
else:
    old5b = """function onOverlayMouseDown(e: MouseEvent) {
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
    new5 = """function onOverlayMouseDown(e: MouseEvent) {
  // Swipe handled by onCanvasMouseDown
}"""
    if old5b in content:
        content = content.replace(old5b, new5)
        print("Fix 5: onOverlayMouseDown minimized")
    else:
        print("WARNING Fix 5: pattern not found")

# Write back
with open(f, "w", encoding="utf-8") as fp:
    fp.write(content)
print(f"Lines: {content.count(chr(10))}")
