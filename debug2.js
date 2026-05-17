const fs = require("fs");
const c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Check startDpadResize
let i = c.indexOf("function startDpadResize");
if (i >= 0) {
  // Show exact content until closing brace
  let end = i;
  let braceCount = 0;
  let foundBrace = false;
  for (let j = i; j < c.length; j++) {
    if (c[j] === "{") { braceCount++; foundBrace = true; }
    else if (c[j] === "}") { braceCount--; }
    if (foundBrace && braceCount === 0) { end = j + 1; break; }
  }
  console.log("startDpadResize:");
  let snippet = c.substring(i, end);
  // Show with visible line endings
  snippet = snippet.replace(/\r/g, "\\r").replace(/\n/g, "\\n");
  console.log(snippet);
  console.log("---");
}

// Check startDrag
i = c.indexOf("function startDrag(e");
if (i >= 0) {
  let end = i;
  let braceCount = 0;
  let foundBrace = false;
  for (let j = i; j < c.length; j++) {
    if (c[j] === "{") { braceCount++; foundBrace = true; }
    else if (c[j] === "}") { braceCount--; }
    if (foundBrace && braceCount === 0) { end = j + 1; break; }
  }
  console.log("startDrag:");
  let snippet = c.substring(i, end);
  snippet = snippet.replace(/\r/g, "\\r").replace(/\n/g, "\\n");
  console.log(snippet);
  console.log("---");
}

// Check swipe create
i = c.indexOf("swp = {");
if (i >= 0) {
  let end = i + 300;
  let snippet = c.substring(i, end);
  snippet = snippet.replace(/\r/g, "\\r").replace(/\n/g, "\\n");
  console.log("swipe create:");
  console.log(snippet);
  console.log("---");
}

// Check resize in move
i = c.indexOf("// DPad resize");
if (i >= 0) {
  let end = i + 300;
  let snippet = c.substring(i, end);
  snippet = snippet.replace(/\r/g, "\\r").replace(/\n/g, "\\n");
  console.log("DPad resize in move:");
  console.log(snippet);
  console.log("---");
}
