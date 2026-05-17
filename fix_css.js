const fs = require("fs");
let css = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", "utf-8");

// Update overlay CSS to not use flex - just absolute inside relative parent
const oldOverlay = `.key-mapping-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
}`;

const newOverlay = `.key-mapping-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 50;
  background: rgba(0, 0, 59, 0.45);
  display: flex;
}

.key-mapping-overlay .key-mapping-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
}`;

if (css.indexOf(oldOverlay) >= 0) {
  css = css.replace(oldOverlay, newOverlay);
  console.log("Updated overlay CSS");
} else {
  console.log("FAIL: oldOverlay not found");
  // Show what we have
  const i = css.indexOf(".key-mapping-overlay");
  if (i >= 0) console.log("Found at " + i + ": " + css.substring(i, i+150).replace(/\r/g,"\\r").replace(/\n/g,"\\n"));
}

// Remove old standalone .key-mapping-canvas CSS
const oldCanvas = `.key-mapping-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
}`;
if (css.indexOf(oldCanvas) >= 0) {
  css = css.replace(oldCanvas, "");
  console.log("Removed old standalone canvas CSS");
}

// Add .dpad-rect and .dpad-circle to inherit size from parent
const dpadRectCSS = `.key-control.dpad .dpad-rect {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform: translate(-50%, -50%);
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.key-control.dpad .dpad-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.5);
  background: rgba(59, 130, 246, 0.15);
}`;

// Find old dpad-rect CSS and replace
const oldDpadRect = `.key-control.dpad .dpad-rect {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 2px dashed rgba(255, 255, 255, 0.3);
}`;
if (css.indexOf(oldDpadRect) >= 0) {
  css = css.replace(oldDpadRect, dpadRectCSS);
  console.log("Updated dpad-rect CSS");
}

// Add .dpad-circle CSS if not present
if (css.indexOf(".key-control.dpad .dpad-circle") < 0) {
  // Insert after dpad-rect
  const dpadRectEnd = css.indexOf(".key-control.dpad .dpad-rect");
  if (dpadRectEnd >= 0) {
    // Find end of that block
    const endBlock = css.indexOf("}", dpadRectEnd);
    css = css.substring(0, endBlock + 1) + "\r\n\r\n" + `.key-control.dpad .dpad-circle {\r\n  position: absolute;\r\n  top: 50%;\r\n  left: 50%;\r\n  width: 100%;\r\n  height: 100%;\r\n  transform: translate(-50%, -50%);\r\n  border-radius: 50%;\r\n  border: 2px solid rgba(255, 255, 255, 0.5);\r\n  background: rgba(59, 130, 246, 0.15);\r\n}` + css.substring(endBlock + 1);
    console.log("Added dpad-circle CSS");
  }
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", css, "utf-8");
console.log("CSS size: " + css.length);
