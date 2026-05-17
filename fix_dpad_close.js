const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Pattern: getDpadKeyStyle's return statement ending with " }" followed immediately by function controlId
// Need to insert a closing } between them
const pattern = "userSelect:\"none\" }" + EOL + "function controlId";
const i = c.indexOf(pattern);
if (i >= 0) {
  // Insert function close brace between the return's } and function controlId
  c = c.substring(0, i + pattern.indexOf(EOL)) + EOL + "}" + EOL + "function controlId" + c.substring(i + pattern.length);
  console.log("Added missing getDpadKeyStyle closing brace");
} else {
  console.log("FAIL: pattern not found");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
