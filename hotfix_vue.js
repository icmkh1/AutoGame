const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Find and remove the orphaned toSessionCoords code
const orphanStart = "} {" + EOL +
  "  if (!canvas.value) return { x: clientX, y: clientY }";
const orphanEnd = "    y: Math.round((clientY - rect.top) / rect.height * sh)," + EOL +
  "  }" + EOL +
  "}";

const iStart = c.indexOf(orphanStart);
if (iStart >= 0) {
  const iEnd = c.indexOf(orphanEnd, iStart) + orphanEnd.length;
  // Replace orphan with just "}" (closing the toNormalizedCoords function)
  c = c.substring(0, iStart) + c.substring(iEnd);
  console.log("Removed orphan toSessionCoords code");
} else {
  console.log("FAIL: orphan not found");
}

// Also check for duplicate closing braces
// Check line } {
c = c.replaceAll("" + EOL + "} {" + EOL, EOL + "}" + EOL);

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
