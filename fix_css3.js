const fs = require("fs");
let css = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", "utf-8");

// Exact match
const oldOverlay = `.key-mapping-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  overflow: hidden;
}`;

const i = css.indexOf(oldOverlay);
if (i >= 0) {
  // Verify it's really there before replacing
  const sample = css.substring(i, i + oldOverlay.length);
  console.log("Found at " + i + ", length: " + sample.length);
  console.log(JSON.stringify(sample));
  console.log(JSON.stringify(oldOverlay));
  console.log("Match: " + (sample === oldOverlay));
  
  css = css.substring(0, i) + `.key-mapping-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 50;
  background: rgba(0, 0, 59, 0.45);
  display: flex;
  overflow: hidden;
}` + css.substring(i + oldOverlay.length);
  console.log("Updated overlay CSS");
} else {
  console.log("FAIL: pattern not found");
  process.exit(1);
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", css, "utf-8");
