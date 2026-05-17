const fs = require("fs");
const EOL = "\r\n";
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const OL = c.length;

// 6: startDpadResize -> add listeners, add onResizeMouseMove, onResizeMouseUp
const OLD_RF = "function startDpadResize(e, dpad) {" + EOL +
  "  resizeTarget = dpad" + EOL +
  "  resizeStartSize = dpad.size" + EOL +
  "  resizeStartMouse = { x: e.clientX, y: e.clientY }" + EOL +
  "}";
const NEW_RF = "function startDpadResize(e, dpad) {" + EOL +
  "  resizeTarget = dpad" + EOL +
  "  resizeStartSize = dpad.size" + EOL +
  "  resizeStartMouse = { x: e.clientX, y: e.clientY }" + EOL +
  "  document.addEventListener('mousemove', onResizeMouseMove)" + EOL +
  "  document.addEventListener('mouseup', onResizeMouseUp)" + EOL +
  "}" + EOL + EOL +
  "function onResizeMouseMove(e) {" + EOL +
  "  if (!resizeTarget || !kmCanvasRef.value) return" + EOL +
  "  const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
  "  const dx = (e.clientX - resizeStartMouse.x) / rect.width" + EOL +
  "  const dy = (e.clientY - resizeStartMouse.y) / rect.height" + EOL +
  "  const delta = Math.max(Math.abs(dx), Math.abs(dy)) * (dx + dy >= 0 ? 1 : -1)" + EOL +
  "  const minSize = 60 / (session.value.width || 1920)" + EOL +
  "  const maxSize = 0.5" + EOL +
  "  resizeTarget.size = Math.max(minSize, Math.min(maxSize, resizeStartSize + delta))" + EOL +
  "}" + EOL + EOL +
  "function onResizeMouseUp() {" + EOL +
  "  resizeTarget = null" + EOL +
  "  document.removeEventListener('mousemove', onResizeMouseMove)" + EOL +
  "  document.removeEventListener('mouseup', onResizeMouseUp)" + EOL +
  "  autoSave()" + EOL +
  "}";

if (c.indexOf(OLD_RF) >= 0) {
  c = c.replace(OLD_RF, NEW_RF);
  console.log("RESIZE_FN: OK");
} else { console.log("RESIZE_FN: NOT FOUND"); }

// 7: Remove old DPad resize from onOverlayMouseMove
const OLD_RIM = "  // DPad resize" + EOL +
  "  if (resizeTarget && kmCanvasRef.value) {" + EOL +
  "    const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
  "    const mx = e.clientX - rect.left + kmCanvasRef.value.scrollLeft" + EOL +
  "    const my = e.clientY - rect.top + kmCanvasRef.value.scrollTop" + EOL +
  "    const dx = mx - resizeStartMouse.x" + EOL +
  "    const dy = my - resizeStartMouse.y" + EOL +
  "    const delta = Math.max(Math.abs(dx), Math.abs(dy))" + EOL +
  "    const newSize = Math.max(60, resizeStartSize + delta)" + EOL +
  "    resizeTarget.size = newSize" + EOL +
  "  }";
if (c.indexOf(OLD_RIM) >= 0) {
  c = c.replace(OLD_RIM, "  // DPad resize moved to onResizeMouseMove");
  console.log("RESIZE_IN_MOVE: OK");
} else { console.log("RESIZE_IN_MOVE: NOT FOUND"); }

// 8: Remove old resize cleanup
const OLD_RC = "  if (resizeTarget) {" + EOL +
  "    resizeTarget = null" + EOL +
  "    autoSave()" + EOL +
  "  }";
if (c.indexOf(OLD_RC) >= 0) {
  c = c.replace(OLD_RC, "  // cleanup by onResizeMouseUp" + EOL + "  resizeTarget = null");
  console.log("RESIZE_CLEAN: OK");
} else { console.log("RESIZE_CLEAN: NOT FOUND"); }

// 9: startDrag - add editingControlId check, normalized coords
const OLD_SD = "function startDrag(e, ctrl, type = \"single\") {" + EOL +
  "  if (!kmCanvasRef.value) return" + EOL +
  "  const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
  "  dragTarget = ctrl" + EOL +
  "  dragType = type" + EOL +
  "  dragOffsetX = e.clientX - rect.left - ctrl.x" + EOL +
  "  dragOffsetY = e.clientY - rect.top - ctrl.y" + EOL +
  "}";
const NEW_SD = "function startDrag(e, ctrl, type = \"single\") {" + EOL +
  "  if (!kmCanvasRef.value) return" + EOL +
  "  if (editingControlId.value) return" + EOL +
  "  const norm = toNormalizedCoords(e.clientX, e.clientY)" + EOL +
  "  dragTarget = ctrl" + EOL +
  "  dragType = type" + EOL +
  "  dragOffsetX = norm.x - ctrl.x" + EOL +
  "  dragOffsetY = norm.y - ctrl.y" + EOL +
  "}";
if (c.indexOf(OLD_SD) >= 0) {
  c = c.replace(OLD_SD, NEW_SD);
  console.log("START_DRAG: OK");
} else { console.log("START_DRAG: NOT FOUND"); }

// 10: execKeyDown/execKeyUp
const OLD_EX = "function execKeyDown(key) {" + EOL +
  "  const mapped = findControlByKey(key)" + EOL +
  "  if (!mapped || !session.value.width || !session.value.height) return" + EOL +
  "  const sw = session.value.width" + EOL +
  "  const sh = session.value.height" + EOL +
  "  if (mapped.kind === \"single\") {" + EOL +
  "    callApi(\"scrcpy_send_touch\", 0, mapped.x, mapped.y, sw, sh).catch(() => {})" + EOL +
  "  } else if (mapped.kind === \"dpad\") {" + EOL +
  "    const dirOffsets = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }" + EOL +
  "    const [dx, dy] = dirOffsets[mapped.dir] || [0, 0]" + EOL +
  "    const dist = mapped.size * 0.4" + EOL +
  "    const ex = Math.round(mapped.x + dx * dist)" + EOL +
  "    const ey = Math.round(mapped.y + dy * dist)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 0, mapped.x, mapped.y, sw, sh).catch(() => {})" + EOL +
  "    callApi(\"scrcpy_send_touch\", 2, ex, ey, sw, sh).catch(() => {})" + EOL +
  "    callApi(\"scrcpy_send_touch\", 1, ex, ey, sw, sh).catch(() => {})" + EOL +
  "  } else if (mapped.kind === \"swipe\" && mapped.path && mapped.path.length > 1) {" + EOL +
  "    callApi(\"key_mapping_swipe\", mapped.path).catch(() => {})" + EOL +
  "  }" + EOL +
  "}" + EOL + EOL +
  "function execKeyUp(key) {" + EOL +
  "  const mapped = findControlByKey(key)" + EOL +
  "  if (!mapped || !session.value.width || !session.value.height) return" + EOL +
  "  const sw = session.value.width" + EOL +
  "  const sh = session.value.height" + EOL +
  "  if (mapped.kind === \"single\") {" + EOL +
  "    callApi(\"scrcpy_send_touch\", 1, mapped.x, mapped.y, sw, sh).catch(() => {})" + EOL +
  "  }" + EOL +
  "}";
const NEW_EX = "function execKeyDown(key) {" + EOL +
  "  const mapped = findControlByKey(key)" + EOL +
  "  if (!mapped || !session.value.width || !session.value.height) return" + EOL +
  "  const sw = session.value.width" + EOL +
  "  const sh = session.value.height" + EOL +
  "  if (mapped.kind === \"single\") {" + EOL +
  "    const sx = Math.round(mapped.x * sw)" + EOL +
  "    const sy = Math.round(mapped.y * sh)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 0, sx, sy, sw, sh).catch(() => {})" + EOL +
  "  } else if (mapped.kind === \"dpad\") {" + EOL +
  "    const sx = Math.round(mapped.x * sw)" + EOL +
  "    const sy = Math.round(mapped.y * sh)" + EOL +
  "    const dirOffsets = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }" + EOL +
  "    const [dx, dy] = dirOffsets[mapped.dir] || [0, 0]" + EOL +
  "    const dist = mapped.size * sw * 0.4" + EOL +
  "    const ex = Math.round(sx + dx * dist)" + EOL +
  "    const ey = Math.round(sy + dy * dist)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 0, sx, sy, sw, sh).catch(() => {})" + EOL +
  "    callApi(\"scrcpy_send_touch\", 2, ex, ey, sw, sh).catch(() => {})" + EOL +
  "    callApi(\"scrcpy_send_touch\", 1, ex, ey, sw, sh).catch(() => {})" + EOL +
  "  } else if (mapped.kind === \"swipe\" && mapped.path && mapped.path.length > 1) {" + EOL +
  "    const pathPx = mapped.path.map(p => ({" + EOL +
  "      x: Math.round(p.x * sw)," + EOL +
  "      y: Math.round(p.y * sh)," + EOL +
  "      delayMs: p.delayMs" + EOL +
  "    }))" + EOL +
  "    callApi(\"key_mapping_swipe\", pathPx).catch(() => {})" + EOL +
  "  }" + EOL +
  "}" + EOL + EOL +
  "function execKeyUp(key) {" + EOL +
  "  const mapped = findControlByKey(key)" + EOL +
  "  if (!mapped || !session.value.width || !session.value.height) return" + EOL +
  "  const sw = session.value.width" + EOL +
  "  const sh = session.value.height" + EOL +
  "  if (mapped.kind === \"single\") {" + EOL +
  "    const sx = Math.round(mapped.x * sw)" + EOL +
  "    const sy = Math.round(mapped.y * sh)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 1, sx, sy, sw, sh).catch(() => {})" + EOL +
  "  }" + EOL +
  "}";

if (c.indexOf(OLD_EX) >= 0) {
  c = c.replace(OLD_EX, NEW_EX);
  console.log("EXEC: OK");
} else { console.log("EXEC: NOT FOUND"); }

// 11: Mouse handlers before handleKeyup
const MOUSE_HD = EOL + EOL +
  "function handleMouseDown(event) {" + EOL +
  "  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {" + EOL +
  "    const btnMap = { 0: \"MLeft\", 1: \"MRight\", 2: \"Middle\", 3: \"MSide1\", 4: \"MSide2\" }" + EOL +
  "    const key = btnMap[event.button]" + EOL +
  "    if (key) execKeyDown(key)" + EOL +
  "  }" + EOL +
  "}" + EOL + EOL +
  "function handleMouseUp(event) {" + EOL +
  "  if (isKeyMappingActive.value && !showKeyMapping.value && status.value.running) {" + EOL +
  "    const btnMap = { 0: \"MLeft\", 1: \"MRight\", 2: \"Middle\", 3: \"MSide1\", 4: \"MSide2\" }" + EOL +
  "    const key = btnMap[event.button]" + EOL +
  "    if (key) execKeyUp(key)" + EOL +
  "  }" + EOL +
  "}" + EOL + EOL;

const HK_MARKER = "function handleKeyup(event)";
const ih = c.indexOf(HK_MARKER);
if (ih >= 0) {
  c = c.substring(0, ih) + MOUSE_HD + c.substring(ih);
  console.log("MOUSE_HANDLERS: OK");
} else { console.log("MOUSE_HANDLERS: NOT FOUND"); }

// 12: Add mouse listeners in onMounted
const OLD_MNT = "window.addEventListener('keydown', handleKeydown)" + EOL +
  "  window.addEventListener('keyup', handleKeyup)" + EOL + EOL +
  "  setupAutoHideEvents()";
const NEW_MNT = "window.addEventListener('keydown', handleKeydown)" + EOL +
  "  window.addEventListener('keyup', handleKeyup)" + EOL +
  "  window.addEventListener('mousedown', handleMouseDown)" + EOL +
  "  window.addEventListener('mouseup', handleMouseUp)" + EOL + EOL +
  "  setupAutoHideEvents()";
if (c.indexOf(OLD_MNT) >= 0) {
  c = c.replace(OLD_MNT, NEW_MNT);
  console.log("MOUNT: OK");
} else { console.log("MOUNT: NOT FOUND"); }

// 13: Cleanup in onBeforeUnmount
const OLD_UM = "window.removeEventListener('keydown', handleKeydown)" + EOL +
  "  window.removeEventListener('keyup', handleKeyup)" + EOL +
  "  teardownKeyCapture()";
const NEW_UM = "window.removeEventListener('keydown', handleKeydown)" + EOL +
  "  window.removeEventListener('keyup', handleKeyup)" + EOL +
  "  window.removeEventListener('mousedown', handleMouseDown)" + EOL +
  "  window.removeEventListener('mouseup', handleMouseUp)" + EOL +
  "  teardownKeyCapture()";
if (c.indexOf(OLD_UM) >= 0) {
  c = c.replace(OLD_UM, NEW_UM);
  console.log("UNMOUNT: OK");
} else { console.log("UNMOUNT: NOT FOUND"); }

// 14: kmResizeObserver in onMounted
const OLD_OBS = "  if (viewport.value) resizeObserver.observe(viewport.value)" + EOL + EOL +
  "  // 添加键盘事件监听";
const NEW_OBS = "  if (viewport.value) resizeObserver.observe(viewport.value)" + EOL + EOL +
  "  // Observe key mapping canvas for resize" + EOL +
  "  if (kmCanvasRef.value) {" + EOL +
  "    kmResizeObserver = new ResizeObserver((entries) => {" + EOL +
  "      const entry = entries[0]" + EOL +
  "      if (entry) {" + EOL +
  "        kmPixelWidth.value = entry.contentRect.width" + EOL +
  "        kmPixelHeight.value = entry.contentRect.height" + EOL +
  "      }" + EOL +
  "    })" + EOL +
  "    kmResizeObserver.observe(kmCanvasRef.value)" + EOL +
  "  }" + EOL + EOL +
  "  // 添加键盘事件监听";
if (c.indexOf(OLD_OBS) >= 0) {
  c = c.replace(OLD_OBS, NEW_OBS);
  console.log("OBSERVE: OK");
} else { console.log("OBSERVE: NOT FOUND"); }

// 15: kmResizeObserver cleanup
const OLD_DISC = "  if (fpsTimer) window.clearInterval(fpsTimer)" + EOL +
  "  resizeObserver?.disconnect()";
const NEW_DISC = "  if (fpsTimer) window.clearInterval(fpsTimer)" + EOL +
  "  resizeObserver?.disconnect()" + EOL +
  "  kmResizeObserver?.disconnect()";
if (c.indexOf(OLD_DISC) >= 0) {
  c = c.replace(OLD_DISC, NEW_DISC);
  console.log("DISC: OK");
} else { console.log("DISC: NOT FOUND"); }

// 16: Auto-hide on close
const OLD_AH = "  // Activate auto-hide mouse if enabled" + EOL +
  "  if (autoHideMouse.value) {" + EOL +
  "    callApi(\"set_key_mapping_auto_hide\", true).catch(() => {})" + EOL +
  "  }";
const NEW_AH = "  // Activate auto-hide mouse if enabled (only on close)" + EOL +
  "  if (autoHideMouse.value) {" + EOL +
  "    callApi(\"set_key_mapping_auto_hide\", true).catch(() => {})" + EOL +
  "  } else {" + EOL +
  "    callApi(\"set_key_mapping_auto_hide\", false).catch(() => {})" + EOL +
  "  }";
if (c.indexOf(OLD_AH) >= 0) {
  c = c.replace(OLD_AH, NEW_AH);
  console.log("AUTO_HIDE: OK");
} else { console.log("AUTO_HIDE: NOT FOUND"); }

// 17: Swipe naming
const OLD_SC = "    const swp = {" + EOL +
  "      id: controlId(\"swp\")," + EOL +
  "      key: \"\"," + EOL +
  "      x: pos.x, y: pos.y," + EOL +
  "      radius: 25," + EOL +
  "      path: [...swipePoints.value]," + EOL +
  "    }" + EOL +
  "    swipes.value.push(swp)" + EOL +
  "    autoSave()";
const NEW_SC = "    const swp = {" + EOL +
  "      id: controlId(\"swp\")," + EOL +
  "      key: \"\"," + EOL +
  "      label: \"\"," + EOL +
  "      x: pos.x, y: pos.y," + EOL +
  "      radius: 25," + EOL +
  "      path: [...swipePoints.value]," + EOL +
  "    }" + EOL +
  "    swipes.value.push(swp)" + EOL +
  "    editingControlId.value = swp.id";
if (c.indexOf(OLD_SC) >= 0) {
  c = c.replace(OLD_SC, NEW_SC);
  console.log("SWIPE: OK");
} else { console.log("SWIPE: NOT FOUND"); }

// Write final
fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("\nSize: " + OL + " -> " + c.length);

// Verify all
const checks = {
  "toNormalizedCoords": "norm coord",
  "ctrlStyle": "ctrl style",
  "getDpadKeyStyle": "dpad style",
  "onResizeMouseMove": "resize fn",
  "handleMouseDown": "mouse down",
  "handleMouseUp": "mouse up",
  "editingControlId.value = swp.id": "swipe naming",
  "Math.round(mapped.x * sw)": "exec conv",
  "norm.x - dragOffsetX": "norm drag",
  "sizeNorm": "norm size",
  "kmPixelWidth": "pixel dim",
  "kmResizeObserver": "obs",
  "pathPx = mapped.path.map": "swipe conv",
  "MLeft": "btn MLeft",
  "MRight": "btn MRight",
  "Middle": "btn Mid",
  "MSide1": "btn S1",
  "MSide2": "btn S2",
};
let ok = true;
for (const [k, v] of Object.entries(checks)) {
  if (!c.includes(k)) {
    console.log("MISS: " + v);
    ok = false;
  }
}
if (ok) console.log("ALL CHECKS PASSED");
