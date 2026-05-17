const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Remove the orphan comment line between onOverlayMouseMove and onOverlayMouseUp
const orphanComment = "    // DPad resize moved (document-level)" + EOL + EOL;
const i = c.indexOf(orphanComment);
if (i >= 0) {
  c = c.substring(0, i) + c.substring(i + orphanComment.length);
  console.log("Removed orphan comment");
} else {
  console.log("FAIL: orphan comment not found");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
