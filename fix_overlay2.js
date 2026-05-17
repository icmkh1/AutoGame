const fs = require("fs");
const EOL = "\r\n";
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");

// === STEP 1: Extract overlay content ===
const overlayComment = "<!-- Key Mapping Overlay -->";
const iComment = c.indexOf(overlayComment);
if (iComment < 0) { console.log("FAIL: overlay comment not found"); process.exit(1); }

// Find the matching close div for the overlay div
// The structure is:
// <div v-if="showKeyMapping" class="key-mapping-overlay" ...>
//   <div class="key-mapping-canvas" ...>
//     ...
//   </div>
//   <!-- Sidebar -->
//   <div class="key-mapping-sidebar">
//     ...
//   </div>
//   <!-- Context menu -->
//   <div v-if="contextMenu.show" class="context-menu" ...>
//     ...
//   </div>
// </div>

// Find the opening <div> of the overlay
const iOverlayOpen = c.indexOf("<div", iComment);

// Count div nesting
let count = 0;
let foundOpen = false;
let iOverlayClose = iOverlayOpen;
for (let i = iOverlayOpen; i < c.length; i++) {
  if (c[i] === "<" && c[i+1] === "d" && c[i+2] === "i" && c[i+3] === "v") {
    // Check if it's a closing tag
    if (c[i+4] === ">" || c[i+4] === " " || (c[i-1] !== '/' && (c[i-1] !== '-' || c[i-2] !== '-'))) {
      // Opening <div or <div ...
      count++;
      foundOpen = true;
    }
  } else if (c.substring(i, i+6) === "</div>") {
    count--;
  }
  if (foundOpen && count === 0) {
    iOverlayClose = i + 6;
    break;
  }
}

console.log("Overlay div: " + iOverlayOpen + " -> " + iOverlayClose);
const overlayFull = c.substring(iComment, iOverlayClose);
console.log("Overlay HTML length: " + overlayFull.length);

// === STEP 2: Remove overlay from current position ===
c = c.substring(0, iComment) + c.substring(iOverlayClose);

// === STEP 3: Insert overlay inside screen-wrapper ===
// Find screen-wrapper close </div>
// The canvas is self-closing <canvas ... />. After that:
// <div class="fps-overlay">..</div>
// <div class="placeholder">..</div>
// </div>  <-- screen-wrapper close

// Find the placeholder close then the screen-wrapper close
const placeholderClose = "        </div>" + EOL + "      </div>";
// But there could be multiple matches. Let's find via viewport structure
// Re-find screen-wrapper open, then find its close
const swOpen = "<div class=\"screen-wrapper\" :style=\"screenStyle\">";
const iSW = c.indexOf(swOpen);
if (iSW < 0) { console.log("FAIL: screen-wrapper not found"); process.exit(1); }

// Count divs from screen-wrapper open to find its matching close
count = 0;
foundOpen = false;
let iSWClose = iSW;
for (let i = iSW; i < c.length; i++) {
  // Check for opening <div (not self-closing)
  if (c.substring(i, i+4) === "<div" && c[i+4] !== 'i' && c[i-1] !== '/') {
    // Make sure it's not a comment or self-closing
    if (c[i+4] === " " || c[i+4] === ">" || c[i+4] === "c" || c[i+4] === "v") {
      count++;
      foundOpen = true;
    }
  } else if (c.substring(i, i+6) === "</div>") {
    count--;
  }
  if (foundOpen && count === 0) {
    iSWClose = i + 6;
    break;
  }
}

console.log("Screen-wrapper: " + iSW + " -> " + iSWClose);

// Insert overlay right before screen-wrapper close
c = c.substring(0, iSWClose - 6) + EOL + overlayFull + c.substring(iSWClose - 6);

console.log("Overlay moved inside screen-wrapper");

// === STEP 4: Fix DPad styles ===
const oldDpadStyle = `:style="{ left: dpad.x + 'px', top: dpad.y + 'px', width: dpad.size + 'px', height: dpad.size + 'px' }"`;
c = c.replace(oldDpadStyle, `:style="ctrlStyle(dpad, true)"`);
console.log("DPad style fixed");

// Fix swipe style too
const oldSwipeStyle = `:style="{ left: swp.x + 'px', top: swp.y + 'px', width: (swp.radius*2) + 'px', height: (swp.radius*2) + 'px' }"`;
c = c.replace(oldSwipeStyle, `:style="ctrlStyle(swp)"`);
console.log("Swipe style fixed");

// Fix dpad-rect and dpad-circle inline styles
c = c.replace(`<div class="dpad-rect" :style="{ width: dpad.size + 'px', height: dpad.size + 'px' }"></div>`, `<div class="dpad-rect"></div>`);
c = c.replace(`<div class="dpad-circle" :style="{ width: dpad.size + 'px', height: dpad.size + 'px' }"></div>`, `<div class="dpad-circle"></div>`);
console.log("DPad rect/circle fixed");

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
