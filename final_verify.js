const fs = require("fs");

console.log("=== VERIFYING ALL FILES ===");
console.log("");

// Check ScreenCastView.vue
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
console.log("ScreenCastView.vue: " + c.length + " bytes");

const checks1 = [
  ["toNormalizedCoords", "Normalized coordinate system"],
  ["ctrlStyle", "Control style helper"],
  ["getDpadKeyStyle", "DPad key style helper"],
  ["onResizeMouseMove", "DPad resize handler"],
  ["onResizeMouseUp", "Resize cleanup"],
  ["handleMouseDown", "Mouse press handler"],
  ["handleMouseUp", "Mouse release handler"],
  ["sizeNorm", "Normalized DPAD size"],
  ["kmPixelWidth", "Pixel width tracking"],
  ["kmResizeObserver", "Resize observer"],
  ["btnMap[event.button]", "Mouse button mapping"],
  ["Math.round(mapped.x * sw)", "Normalized->session conversion"],
  ["pathPx = mapped.path.map", "Swipe path conversion"],
  ["norm.x - dragOffsetX", "Normalized drag"],
  ["editingControlId.value = swp.id", "Swipe wait-for-key naming"],
  ["exec_key_mapping_down", "Backend executor notification"],
  ["exec_key_mapping_up", "Backend executor notification"],
  ["MLeft", "Mouse button MLeft"],
  ["MRight", "Mouse button MRight"],
  ["Middle", "Mouse button Middle"],
  ["MSide1", "Mouse button MSide1"],
  ["MSide2", "Mouse button MSide2"],
];
let ok1 = true;
for (const [k, v] of checks1) {
  if (!c.includes(k)) {
    console.log("  MISS: " + v + " (" + k + ")");
    ok1 = false;
  }
}
if (ok1) console.log("  ALL FRONTEND CHECKS PASSED (" + checks1.length + ")");

console.log("");

// Check scrcpy_manager.py
c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\src\\scrcpy_manager.py", "utf-8");
console.log("scrcpy_manager.py: " + c.length + " bytes");
const checks2 = [
  ["send_normalized_touch", "Normalized touch method"],
  ["key_mapping_swipe", "Swipe execution"],
  ["_send_swipe_async", "Async swipe"],
  ["apply_key_mapping", "Apply mapping"],
  ["remove_key_mapping", "Remove mapping"],
  ["_last_session", "Session size tracking"],
];
let ok2 = true;
for (const [k, v] of checks2) {
  if (!c.includes(k)) {
    console.log("  MISS: " + v + " (" + k + ")");
    ok2 = false;
  }
}
if (ok2) console.log("  ALL SCRCPY CHECKS PASSED (" + checks2.length + ")");

console.log("");

// Check api.py
c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\src\\api.py", "utf-8");
console.log("api.py: " + c.length + " bytes");
const checks3 = [
  ["KeyMappingExecutor", "Executor import"],
  ["send_normalized_touch", "Normalized touch API"],
  ["exec_key_mapping_down", "Executor down API"],
  ["exec_key_mapping_up", "Executor up API"],
  ["get_key_mapping_mapped_keys", "Mapped keys API"],
  ["self.key_mapping_executor.apply(data)", "Auto-apply executor"],
];
let ok3 = true;
for (const [k, v] of checks3) {
  if (!c.includes(k)) {
    console.log("  MISS: " + v + " (" + k + ")");
    ok3 = false;
  }
}
if (ok3) console.log("  ALL API CHECKS PASSED (" + checks3.length + ")");

console.log("");

// Check key_mapping_executor.py
c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\src\\key_mapping_executor.py", "utf-8");
console.log("key_mapping_executor.py: " + c.length + " bytes");
const checks4 = [
  ["send_normalized_touch", "Normalized touch call"],
  ["on_key_down", "Key down handler"],
  ["on_key_up", "Key up handler"],
  ["get_mapped_keys", "Get mapped keys"],
  ["dpad", "DPad handling"],
  ["swipe", "Swipe handling"],
];
let ok4 = true;
for (const [k, v] of checks4) {
  if (!c.includes(k)) {
    console.log("  MISS: " + v + " (" + k + ")");
    ok4 = false;
  }
}
if (ok4) console.log("  ALL EXECUTOR CHECKS PASSED (" + checks4.length + ")");

console.log("");

if (ok1 && ok2 && ok3 && ok4) {
  console.log("=== ALL VERIFICATIONS PASSED ===");
} else {
  console.log("=== SOME CHECKS FAILED ===");
}
