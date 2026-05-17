const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// The toNormalizedCoords function is missing its closing }
// Current: 
//   return {
//     x: ...,
//     y: ...,
//   }
//   const renamingFile = ...
// 
// Should be:
//   return {
//     x: ...,
//     y: ...,
//   }
// }
// const renamingFile = ...

// Find the pattern: closing } of return object followed immediately by const renamingFile
const pattern = "  }" + EOL + "const renamingFile";
const i = c.indexOf(pattern);
if (i >= 0) {
  // Insert the function closing brace
  c = c.substring(0, i) + "  }" + EOL + "}" + EOL + "const renamingFile" + c.substring(i + pattern.length);
  console.log("Added missing function closing brace");
} else {
  console.log("FAIL: pattern not found");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
