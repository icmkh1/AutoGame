const fs = require("fs");
const EOL = "\r\n";
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const OL = c.length;

// Fix startDpadResize (with type annotations)
const OLD_RF = "function startDpadResize(e: MouseEvent, dpad: any) {" + EOL +
  "  resizeTarget = dpad" + EOL +
  "  resizeStartSize = dpad.size" + EOL +
  "  resizeStartMouse = { x: e.clientX, y: e.clientY }" + EOL +
  "}";
const NEW_RF = "function startDpadResize(e: MouseEvent, dpad: any) {" + EOL +
  "  resizeTarget = dpad" + EOL +
  "  resizeStartSize = dpad.size" + EOL +
  "  resizeStartMouse = { x: e.clientX, y: e.clientY }" + EOL +
  "  document.addEventListener('mousemove', onResizeMouseMove)" + EOL +
  "  document.addEventListener('mouseup', onResizeMouseUp)" + EOL +
  "}" + EOL + EOL +
  "function onResizeMouseMove(e: MouseEvent) {" + EOL +
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

// Fix DPad resize in move (uses resizeTarget.x, not resizeStartMouse.x)
// Find the exact resize block in onOverlayMouseMove
const i = c.indexOf("// DPad resize");
if (i >= 0) {
  // Read until we hit 2 blank lines or the closing }
  let j = i;
  while (j < c.length && c[j] !== "}") j++;
  const block = c.substring(i, j + 1);
  console.log("Found resize block:");
  console.log(block.substring(0, 200).replace(/\r/g,"\\r").replace(/\n/g,"\\n"));
  const newBlock = "  // DPad resize moved to onResizeMouseMove" + EOL +
    "  // (handled by document-level listeners)";
  c = c.replace(block, newBlock);
  console.log("RESIZE_IN_MOVE: OK");
} else { console.log("DPAD_RESIZE: NOT FOUND"); }

// Fix startDrag (different calculation pattern)
const OLD_SD = "function startDrag(e: MouseEvent, ctrl: any, type = \"single\") {" + EOL +
  "  if (!kmCanvasRef.value) return" + EOL +
  "  const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
  "  dragTarget = ctrl" + EOL +
  "  dragType = type" + EOL +
  "  dragOffsetX = e.clientX - rect.left + kmCanvasRef.value.scrollLeft - ctrl.x" + EOL +
  "  dragOffsetY = e.clientY - rect.top + kmCanvasRef.value.scrollTop - ctrl.y" + EOL +
  "}";
const NEW_SD = "function startDrag(e: MouseEvent, ctrl: any, type = \"single\") {" + EOL +
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

// Write
fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + OL + " -> " + c.length);
console.log("onResizeMouseMove: " + c.includes("onResizeMouseMove"));
console.log("norm.x - ctrl.x: " + c.includes("norm.x - ctrl.x"));
