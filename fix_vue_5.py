f = "temp_f5.vue"
with open(f, "r", encoding="utf-8") as fp:
    c = fp.read()

changes = []

# Fix 1: Coordinate conversion helper + session access
# Add a function to convert pixel coords to session coords
coord_helper = """
function toSessionCoords(clientX: number, clientY: number): {x:number, y:number} {
  if (!canvas.value) return { x: clientX, y: clientY }
  const rect = canvas.value.getBoundingClientRect()
  const sw = session.value.width || 1
  const sh = session.value.height || 1
  return {
    x: Math.round((clientX - rect.left) / rect.width * sw),
    y: Math.round((clientY - rect.top) / rect.height * sh),
  }
}
"""

# Insert after `const swipeStartTime = ref(0)`
old_anchor = "const swipeStartTime = ref(0)"
new_anchor = old_anchor + coord_helper.rstrip()
if old_anchor in c:
    c = c.replace(old_anchor, new_anchor)
    changes.append("coord helper added")

# Fix 2: onCanvasMouseDown - use toSessionCoords
old_cmd = """function onCanvasMouseDown(e: MouseEvent) {
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

new_cmd = """function onCanvasMouseDown(e: MouseEvent) {
  if (!kmCanvasRef.value) return
  contextMenu.value.show = false
  if (pendingSwipe.value) {
    pendingSwipe.value = false
    isRecordingSwipe.value = true
    swipePoints.value = []
    const pos = toSessionCoords(e.clientX, e.clientY)
    swipePoints.value = [{ x: pos.x, y: pos.y, delayMs: 0 }]
    swipeStartTime.value = Date.now()
    return
  }
  if (isRecordingSwipe.value) return"""

if old_cmd in c:
    c = c.replace(old_cmd, new_cmd)
    changes.append("onCanvasMouseDown uses session coords")
else:
    changes.append("WARNING: onCanvasMouseDown pattern not found")

# Fix 3: newControlAt - use toSessionCoords
old_nca = """function newControlAt(e: MouseEvent) {
  if (!overlayRef.value || !kmCanvasRef.value) return
  contextMenu.value.show = false
  if (isRecordingSwipe.value) return
  const rect = kmCanvasRef.value.getBoundingClientRect()"""

new_nca = """function newControlAt(e: MouseEvent) {
  if (!overlayRef.value || !kmCanvasRef.value) return
  contextMenu.value.show = false
  if (isRecordingSwipe.value) return
  const pos = toSessionCoords(e.clientX, e.clientY)"""

if old_nca in c:
    c = c.replace(old_nca, new_nca)
    changes.append("newControlAt uses session coords")
    # Also fix the x,y references inside the function
    c = c.replace("const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)", "")
    c = c.replace("const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)", "")
    # Remove blank lines left behind
    c = c.replace("const pos = toSessionCoords(e.clientX, e.clientY)\n\n  const ctrl", "const pos = toSessionCoords(e.clientX, e.clientY)\n  const ctrl")
    c = c.replace("pos.x, y:", "pos.x,\n    y:")
    c = c.replace("const ctrl = {\n    id: controlId(\"ctrl\"),\n    key: \"\",\n    label: \"\",\n    x, y,", "const ctrl = {\n    id: controlId(\"ctrl\"),\n    key: \"\",\n    label: \"\",\n    x: pos.x, y: pos.y,")
    changes.append("fixed control creation coords")
else:
    changes.append("WARNING: newControlAt pattern not found")

# Fix 4: Swipe record in onOverlayMouseDown - use session coords
old_omd = """function onOverlayMouseDown(e: MouseEvent) {
  // Swipe handled by onCanvasMouseDown
}"""
if old_omd in c:
    changes.append("onOverlayMouseDown already minimal, OK")
else:
    # Find the actual text
    old_omd2 = """function onOverlayMouseDown(e: MouseEvent) {
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
    new_omd2 = """function onOverlayMouseDown(e: MouseEvent) {
  // Swipe recording handled by onCanvasMouseDown
}"""
    if old_omd2 in c:
        c = c.replace(old_omd2, new_omd2)
        changes.append("onOverlayMouseDown minimized")
    else:
        changes.append("WARNING: onOverlayMouseDown pattern not found")

# Fix 5: Swipe recording points in onOverlayMouseMove - use session coords
old_mm = """function onOverlayMouseMove(e: MouseEvent) {
  if (isRecordingSwipe.value && swipeStartTime.value > 0 && kmCanvasRef.value) {
    const rect = kmCanvasRef.value.getBoundingClientRect()
    const x = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft)
    const y = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop)
    const delay = Date.now() - swipeStartTime.value
    const last = swipePoints.value[swipePoints.value.length - 1]"""

new_mm = """function onOverlayMouseMove(e: MouseEvent) {
  if (isRecordingSwipe.value && swipeStartTime.value > 0 && kmCanvasRef.value) {
    const pos = toSessionCoords(e.clientX, e.clientY)
    const x = pos.x
    const y = pos.y
    const delay = Date.now() - swipeStartTime.value
    const last = swipePoints.value[swipePoints.value.length - 1]"""

if old_mm in c:
    c = c.replace(old_mm, new_mm)
    changes.append("swipe move uses session coords")
else:
    changes.append("WARNING: swipe move pattern not found")

# Fix 6: Swipe end in onOverlayMouseUp - use session coords + wait for key press
old_mu = """function onOverlayMouseUp(e: MouseEvent) {
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
  }"""

new_mu = """function onOverlayMouseUp(e: MouseEvent) {
  if (isRecordingSwipe.value && swipePoints.value.length > 0 && kmCanvasRef.value) {
    isRecordingSwipe.value = false
    const pos = toSessionCoords(e.clientX, e.clientY)
    const ex = pos.x
    const ey = pos.y
    // Add last point scaled to session cords
    const lastDelay = Date.now() - swipeStartTime.value
    const lastPt = swipePoints.value[swipePoints.value.length - 1]
    if (!lastPt || lastPt.x !== ex || lastPt.y !== ey) {
      swipePoints.value.push({ x: ex, y: ey, delayMs: lastDelay })
    }
    const swp = {
      id: controlId("swp"),
      label: "",
      key: "",
      x: ex, y: ey,
      radius: 25,
      path: swipePoints.value.map(p => ({ ...p })),
    }
    swipes.value.push(swp)
    editingControlId.value = swp.id
    swipePoints.value = []
    swipeStartTime.value = 0
  }"""

if old_mu in c:
    c = c.replace(old_mu, new_mu)
    changes.append("swipe end uses session coords + waits for key")
else:
    changes.append("WARNING: swipe end pattern not found")

# Fix 7: Add mouse button capture support
# In setupKeyCapture, also listen for mousedown
old_setup = """function setupKeyCapture() {
  if (keyCaptureHandler) return
  keyCaptureHandler = (e: KeyboardEvent) => {"""

new_setup = """function setupKeyCapture() {
  if (keyCaptureHandler) return
  // Capture keyboard keys
  const mouseBtnMap: Record<number, string> = { 0: "MLeft", 1: "MRight", 2: "Middle", 3: "MSide1", 4: "MSide2" }
  const mouseHandler = (e: MouseEvent) => {
    if (e.button > 4) return
    if (!editingControlId.value && !editingDpadId.value) return
    const btnName = mouseBtnMap[e.button]
    // Check for single/swipe controls
    if (editingControlId.value) {
      const ctrl = [...controls.value, ...swipes.value].find(c => c.id === editingControlId.value)
      if (ctrl) {
        const dup = [...controls.value, ...swipes.value].find(c => c.id !== ctrl.id && c.key === btnName)
        if (!dup) {
          ctrl.key = btnName
          ctrl.label = btnName
        }
        editingControlId.value = null
        autoSave()
      }
    }
    // Check for dpad keys
    if (editingDpadId.value && editingDpadDir.value) {
      const dpad = dpads.value.find(d => d.id === editingDpadId.value)
      if (dpad) {
        dpad.keys[editingDpadDir.value] = { key: btnName, label: btnName }
      }
      editingDpadId.value = null
      editingDpadDir.value = null
      autoSave()
    }
  }
  document.addEventListener("mousedown", mouseHandler, true)
  
  keyCaptureHandler = (e: KeyboardEvent) => {"""

if old_setup in c:
    c = c.replace(old_setup, new_setup)
    changes.append("mouse button capture added")
else:
    changes.append("WARNING: setupKeyCapture pattern not found")

# Fix 8: teardownKeyCapture - also remove mouse handler
old_teardown = """function teardownKeyCapture() {
  if (keyCaptureHandler) {
    document.removeEventListener("keydown", keyCaptureHandler, true)
    keyCaptureHandler = null
  }
}"""
new_teardown = """let mouseCaptureHandler: ((e: MouseEvent) => void) | null = null

function teardownKeyCapture() {
  if (keyCaptureHandler) {
    document.removeEventListener("keydown", keyCaptureHandler, true)
    keyCaptureHandler = null
  }
  if (mouseCaptureHandler) {
    document.removeEventListener("mousedown", mouseCaptureHandler, true)
    mouseCaptureHandler = null
  }
}"""

if old_teardown in c:
    c = c.replace(old_teardown, new_teardown)
    changes.append("teardownKeyCapture updated")
else:
    changes.append("WARNING: teardown pattern not found")

# Fix 9: setupKeyCapture needs to store mouseCaptureHandler
# The new setup has the handler as a local const - need to change to store as variable
old_mhandler = "const mouseHandler = (e: MouseEvent) => {"
new_mhandler = "mouseCaptureHandler = (e: MouseEvent) => {"
if old_mhandler in c:
    c = c.replace(old_mhandler, new_mhandler)
    changes.append("mouseCaptureHandler as module var")
else:
    changes.append("WARNING: mouseHandler var not found")

# Fix 10: In setupKeyCapture, remove the old mouseHandler addEventListener and use the var
old_addmouse = 'document.addEventListener("mousedown", mouseHandler, true)'
new_addmouse = 'document.addEventListener("mousedown", mouseCaptureHandler, true)'
if old_addmouse in c:
    c = c.replace(old_addmouse, new_addmouse)
    changes.append("mouse event listener uses var")
else:
    changes.append("WARNING: mouse event listener not found")

with open(f, "w", encoding="utf-8") as fp:
    fp.write(c)

for ch in changes:
    print(ch)
print(f"Lines: {c.count(chr(10))}")
