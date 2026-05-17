const fs = require("fs");
const EOL = "\r\n";
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");

// ======= MOVE OVERLAY INSIDE SCREEN-WRAPPER =======
// Find the overlay section and move it inside screen-wrapper

// The screen-wrapper structure:
// <div class="screen-wrapper" :style="screenStyle">
//   <canvas ... />
//   <div class="fps-overlay" ...>...</div>
//   <div v-if="!session.width" class="placeholder">...</div>
// </div>
// <!-- Key Mapping Overlay -->
// <div v-if="showKeyMapping" class="key-mapping-overlay" ...>

// We need to move the overlay div INSIDE screen-wrapper, before its closing </div>

const swClose = "      </div>" + EOL + "      <!-- Key Mapping Overlay -->";
const iSW = c.indexOf(swClose);
if (iSW < 0) { console.log("FAIL: swClose not found"); process.exit(1); }

// Find the end of the overlay div (find the closing </div> of the overlay that matches its opening)
const overlayDivStart = c.indexOf("<!-- Key Mapping Overlay -->");
const overlayHtmlStart = c.indexOf("<div", overlayDivStart);

// Count div nesting to find the matching close
let count = 0;
let foundOpen = false;
let overlayCloseIdx = overlayHtmlStart;
for (let i = overlayHtmlStart; i < c.length; i++) {
  if (c.substring(i, i+4) === "<div" && c[i-1] !== '/') { count++; foundOpen = true; }
  else if (c.substring(i, i+6) === "</div>") { count--; }
  if (foundOpen && count === 0) { overlayCloseIdx = i + 6; break; }
}

const overlayContent = c.substring(overlayDivStart, overlayCloseIdx);
const restAfterOverlay = c.substring(overlayCloseIdx);

console.log("Overlay content length: " + overlayContent.length);

// Remove overlay from its current position
c = c.substring(0, overlayDivStart) + restAfterOverlay;

// Insert overlay INSIDE screen-wrapper, before its closing </div>
// The screen-wrapper close is now at the position where swClose started, minus the overlay
// Re-find screen-wrapper close
const newSWClose = "      </div>" + EOL + "      <!-- Key Mapping Overlay -->";
// Actually the overlay was removed, so screen-wrapper close is: "      </div>" followed by whatever was after
// Let's find it differently - find the screen-wrapper div by its unique content
// The canvas ref is inside screen-wrapper. Find canvas closing then find matching </div>
const canvasCloseIdx = c.indexOf("</canvas>");
if (canvasCloseIdx < 0) { console.log("FAIL: canvas not found"); process.exit(1); }

// Find the screen-wrapper's closing </div> after canvas
// The structure after canvas: fps-overlay, placeholder, </div> (screen-wrapper)
let swEnd = canvasCloseIdx + 9; // after </canvas>
count = 0;
foundOpen = false;
for (let i = swEnd; i < c.length; i++) {
  if (c.substring(i, i+4) === "<div" && (i === 0 || c[i-1] !== '/')) { count++; foundOpen = true; }
  else if (c.substring(i, i+6) === "</div>") {
    if (foundOpen && count === 0) { swEnd = i + 6; break; }
    count--;
  }
}

console.log("Inserting overlay at: " + swEnd + " (after placeholder close, before screen-wrapper close)");

// Insert overlay right before screen-wrapper's </div>
// The overlay content has the opening div, sidebar, etc.
// Remove the opening "<!-- Key Mapping Overlay -->" from overlay content since it needs to be inside
// Actually keep the comment so it's clear
c = c.substring(0, swEnd) + EOL + overlayContent + c.substring(swEnd);

// ======= FIX DPad template to use normalized coords =======
// Replace old DPad style with ctrlStyle(dpad, true)
const oldDpadStyle = `:style="{ left: dpad.x + 'px', top: dpad.y + 'px', width: dpad.size + 'px', height: dpad.size + 'px' }" @mousedown.left.stop="startDrag($event, dpad, 'dpad')">`;
const newDpadStyle = `:style="ctrlStyle(dpad, true)" @mousedown.left.stop="startDrag($event, dpad, 'dpad')">`;
c = c.replace(oldDpadStyle, newDpadStyle);
console.log("DPad style fixed: " + c.includes("ctrlStyle(dpad, true)"));

// Fix dpad-rect and dpad-circle styles too
c = c.replace(
  `<div class="dpad-rect" :style="{ width: dpad.size + 'px', height: dpad.size + 'px' }"></div>`,
  `<div class="dpad-rect"></div>`
);
c = c.replace(
  `<div class="dpad-circle" :style="{ width: dpad.size + 'px', height: dpad.size + 'px' }"></div>`,
  `<div class="dpad-circle"></div>`
);
console.log("DPad rect/circle fixed");

// ======= UPDATE CSS for overlay =======
// Update overlay CSS from flex to absolute positioning matching screen-wrapper
const oldCSS = `.key-mapping-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
}`;
const newCSS = `.key-mapping-overlay {
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
// Read CSS file
let cssContent = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", "utf-8");
if (cssContent.indexOf(oldCSS) >= 0) {
  cssContent = cssContent.replace(oldCSS, newCSS);
  console.log("CSS updated");
}

// Remove the old standalone .key-mapping-canvas CSS if it exists
const oldCanvasCSS = `.key-mapping-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
}`;
// It's now inside the overlay block, so remove old standalone version if present
if (cssContent.indexOf(oldCanvasCSS) >= 0) {
  cssContent = cssContent.replace(oldCanvasCSS, '');
  console.log("Removed old standalone canvas CSS");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", cssContent, "utf-8");
console.log("\nDone. Vue size: " + c.length + ", CSS size: " + cssContent.length);
