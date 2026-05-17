const fs = require("fs");
const c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");

const results = {
  "toNormalizedCoords": "normalized coordinate system",
  "ctrlStyle": "control style helper",
  "getDpadKeyStyle": "dpad key styling",
  "onResizeMouseMove": "dpad resize handler",
  "onResizeMouseUp": "resize cleanup",
  "handleMouseDown": "mouse press handler",
  "handleMouseUp": "mouse release handler",
  "sizeNorm": "normalized dpad size",
  "kmPixelWidth": "pixel dimension tracking",
  "kmResizeObserver": "resize observer",
  "btnMap[event.button]": "mouse button mapping",
  "MLeft": "mouse button MLeft",
  "MRight": "mouse button MRight",
  "Middle": "mouse button Middle",
  "MSide1": "mouse button MSide1",
  "MSide2": "mouse button MSide2",
  "Math.round(mapped.x * sw)": "exec normalized->session conversion",
  "pathPx = mapped.path.map": "swipe path conversion",
  "mapped.size * sw * 0.4": "dpad swipe distance",
  "norm.x - dragOffsetX": "normalized drag",
  "norm.x - ctrl.x": "normalized drag offset",
  "editingControlId.value = swp.id": "swipe naming after creation",
  "label: \"\",": "empty swipe label",
  "km-show-cursor": "auto-hide cursor show",
  "km-hide-cursor": "auto-hide cursor hide",
  "mapped.kind": "control type routing",
};

let allOk = true;
let okCount = 0;
for (const [pattern, desc] of Object.entries(results)) {
  const found = c.includes(pattern);
  if (!found) {
    console.log("MISS: " + desc);
    allOk = false;
  } else {
    okCount++;
  }
}
console.log("");
console.log(okCount + "/" + Object.keys(results).length + " checks passed");

// Check for old pattern that should be gone
if (c.includes("toSessionCoords")) {
  console.log("WARN: toSessionCoords still present");
}
if (c.includes("resizeStartMouse")) {
  console.log("WARN: resizeStartMouse still used in onOverlayMouseMove");
}
console.log("Size: " + c.length);
