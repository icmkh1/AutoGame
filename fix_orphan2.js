const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Find the area where the function close brace should be
// After the dragTarget block's closing }, we need another } to close onOverlayMouseMove
// Pattern: "  }", blank line, "    // DPad resize moved"
// But we need "  }\r\n}\r\n" between the drag block's } and the comment

const marker = "    dragTarget.y = Math.max(0, Math.min(1, norm.y - dragOffsetY))" + EOL +
  "  }" + EOL + EOL +
  "    // DPad resize moved to onResizeMouseMove (document-level)";

const i = c.indexOf(marker);
if (i >= 0) {
  const fixed = "    dragTarget.y = Math.max(0, Math.min(1, norm.y - dragOffsetY))" + EOL +
    "  }" + EOL +
    "}" + EOL + EOL +
  "    // DPad resize moved (document-level)";
  c = c.substring(0, i) + fixed + c.substring(i + marker.length);
  console.log("Fixed function close brace");
} else {
  console.log("FAIL: marker not found");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
