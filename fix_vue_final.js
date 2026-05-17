const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\temp_f5.vue", "utf-8");
const OL = c.length;
const EOL = "\r\n";

// 1: Replace toSessionCoords function
const oldFn = "function toSessionCoords(";
const i1 = c.indexOf(oldFn);
if (i1 >= 0) {
  const end1 = c.indexOf("}", i1) + 1;
  const nFn = "function toNormalizedCoords(clientX, clientY) {" + EOL +
    "  if (!kmCanvasRef.value) return { x: 0, y: 0 }" + EOL +
    "  const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
    "  if (rect.width <= 0 || rect.height <= 0) return { x: 0, y: 0 }" + EOL +
    "  return {" + EOL +
    "    x: (clientX - rect.left) / rect.width," + EOL +
    "    y: (clientY - rect.top) / rect.height," + EOL +
    "  }" + EOL +
    "}";
  c = c.substring(0, i1) + nFn + c.substring(end1);
}
c = c.replaceAll("toSessionCoords(", "toNormalizedCoords(");

// 2: Add helpers
const m2 = "}" + EOL + EOL + "function controlId";
const i2 = c.indexOf(m2);
if (i2 >= 0) {
  const hp = EOL +
    "const kmPixelWidth = ref(1)" + EOL +
    "const kmPixelHeight = ref(1)" + EOL +
    "let kmResizeObserver = null" + EOL + EOL +
    "function ctrlStyle(item, isDpad = false) {" + EOL +
    "  const pw = kmPixelWidth.value, ph = kmPixelHeight.value" + EOL +
    "  if (isDpad) {" + EOL +
    "    const s = (item.size || 0.06) * pw" + EOL +
    "    return { left: (item.x*pw - s/2)+\"px\", top: (item.y*ph - s/2)+\"px\", width: s+\"px\", height: s+\"px\" }" + EOL +
    "  }" + EOL +
    "  const sw = session.value.width || 1920" + EOL +
    "  const r = (item.radius || 25) * (pw/sw)" + EOL +
    "  return { left: (item.x*pw - r)+\"px\", top: (item.y*ph - r)+\"px\", width: (r*2)+\"px\", height: (r*2)+\"px\" }" + EOL +
    "}" + EOL + EOL +
    "function getDpadKeyStyle(dpad, dir) {" + EOL +
    "  const pw = kmPixelWidth.value" + EOL +
    "  const s = (dpad.size || 0.06) * pw, r = s/2, o = r*0.55" + EOL +
    "  const a = {up:-90,down:90,left:180,right:0}[dir] * Math.PI/180" + EOL +
    "  return { left: (r+o*Math.cos(a)-16)+\"px\", top: (r+o*Math.sin(a)-12)+\"px\", width:\"32px\", height:\"24px\", lineHeight:\"24px\", textAlign:\"center\", fontSize:\"14px\", position:\"absolute\", cursor:\"pointer\", background:\"rgba(255,255,255,0.2)\", borderRadius:\"4px\", color:\"#fff\", userSelect:\"none\" }" + EOL +
    "}";
  c = c.substring(0, i2 + m2.length) + hp + c.substring(i2 + m2.length);
}

// 3: Template style
c = c.replace(":style=\"{ left: ctrl.x + 'px', top: ctrl.y + 'px', width: (ctrl.radius*2) + 'px', height: (ctrl.radius*2) + 'px' }\"", ":style=\"ctrlStyle(ctrl)\"");

// 4: createDirectionKey
const CDK_OLD = "function createDirectionKey() {" + EOL +
  "  contextMenu.value.show = false" + EOL +
  "  if (!kmCanvasRef.value) return" + EOL +
  "  const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
  "  const cx = Math.round(contextMenu.value.x - rect.left + kmCanvasRef.value.scrollLeft)" + EOL +
  "  const cy = Math.round(contextMenu.value.y - rect.top + kmCanvasRef.value.scrollTop)" + EOL +
  "  const dpad = {" + EOL +
  "    id: controlId(\"dpad\")," + EOL +
  "    x: cx, y: cy," + EOL +
  "    size: 120," + EOL +
  "    keys: {" + EOL +
  "      up: { key: \"W\", label: \"W\" }," + EOL +
  "      down: { key: \"S\", label: \"S\" }," + EOL +
  "      left: { key: \"A\", label: \"A\" }," + EOL +
  "      right: { key: \"D\", label: \"D\" }," + EOL +
  "    }" + EOL +
  "  }" + EOL +
  "  dpads.value.push(dpad)" + EOL +
  "  autoSave()" + EOL +
  "}";

const CDK_NEW = "function createDirectionKey() {" + EOL +
  "  contextMenu.value.show = false" + EOL +
  "  if (!kmCanvasRef.value) return" + EOL +
  "  const norm = toNormalizedCoords(contextMenu.value.x, contextMenu.value.y)" + EOL +
  "  const sizeNorm = 120 / (session.value.width || 1920)" + EOL +
  "  const dpad = {" + EOL +
  "    id: controlId(\"dpad\")," + EOL +
  "    x: norm.x, y: norm.y," + EOL +
  "    size: sizeNorm," + EOL +
  "    keys: {" + EOL +
  "      up: { key: \"W\", label: \"W\" }," + EOL +
  "      down: { key: \"S\", label: \"S\" }," + EOL +
  "      left: { key: \"A\", label: \"A\" }," + EOL +
  "      right: { key: \"D\", label: \"D\" }," + EOL +
  "    }" + EOL +
  "  }" + EOL +
  "  dpads.value.push(dpad)" + EOL +
  "  autoSave()" + EOL +
  "}";

if (c.indexOf(CDK_OLD) >= 0) {
  c = c.replace(CDK_OLD, CDK_NEW);
  console.log("CDK: OK");
} else {
  console.log("CDK: NOT FOUND");
}

// 5: Drag handling
const DRAG_OLD = "  // Drag handling" + EOL +
  "  if (dragTarget) {" + EOL +
  "    if (!kmCanvasRef.value) return" + EOL +
  "    const rect = kmCanvasRef.value.getBoundingClientRect()" + EOL +
  "    const newX = Math.round(e.clientX - rect.left + kmCanvasRef.value.scrollLeft - dragOffsetX)" + EOL +
  "    const newY = Math.round(e.clientY - rect.top + kmCanvasRef.value.scrollTop - dragOffsetY)" + EOL +
  "    dragTarget.x = Math.max(0, newX)" + EOL +
  "    dragTarget.y = Math.max(0, newY)" + EOL +
  "  }";

const DRAG_NEW = "  // Drag handling (normalized coords)" + EOL +
  "  if (dragTarget) {" + EOL +
  "    if (!kmCanvasRef.value) return" + EOL +
  "    const norm = toNormalizedCoords(e.clientX, e.clientY)" + EOL +
  "    dragTarget.x = Math.max(0, Math.min(1, norm.x - dragOffsetX))" + EOL +
  "    dragTarget.y = Math.max(0, Math.min(1, norm.y - dragOffsetY))" + EOL +
  "  }";

if (c.indexOf(DRAG_OLD) >= 0) {
  c = c.replace(DRAG_OLD, DRAG_NEW);
  console.log("DRAG: OK");
} else {
  console.log("DRAG: NOT FOUND");
}

// Write
fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + OL + " -> " + c.length);
console.log("toNormalizedCoords: " + c.includes("toNormalizedCoords"));
console.log("ctrlStyle: " + c.includes("ctrlStyle"));
console.log("getDpadKeyStyle: " + c.includes("getDpadKeyStyle"));
console.log("kmPixelWidth: " + c.includes("kmPixelWidth"));
console.log("kmResizeObserver: " + c.includes("kmResizeObserver"));
console.log("sizeNorm: " + c.includes("sizeNorm"));
