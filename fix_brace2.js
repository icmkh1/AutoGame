const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Pattern: closing } of return object, blank line, then const renamingFile
const pattern = "  }" + EOL + EOL + "const renamingFile";
const i = c.indexOf(pattern);
if (i >= 0) {
  // Insert the function closing brace between the return's } and the blank line
  c = c.substring(0, i) + "  }" + EOL + "}" + EOL + EOL + "const renamingFile" + c.substring(i + pattern.length);
  console.log("Added missing function closing brace");
} else {
  console.log("FAIL: pattern not found");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
