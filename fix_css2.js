const fs = require("fs");
let css = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", "utf-8");

const oldOverlay = `.key-mapping-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  overflow: hidden;
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
  overflow: hidden;
}`;

if (css.indexOf(oldOverlay) >= 0) {
  css = css.replace(oldOverlay, newOverlay);
  console.log("Updated overlay CSS");
} else {
  console.log("FAIL");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.css", css, "utf-8");
