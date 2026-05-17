const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Find the broken section: helpers inserted between "function controlId" and "(prefix: string): string {"
const brokenMarker = "function controlId" + EOL +
  "const kmPixelWidth = ref(1)";

const iBroken = c.indexOf(brokenMarker);
if (iBroken >= 0) {
  // Find where the "getDpadKeyStyle" function ends and the original "controlId" continues
  const afterHelpers = "}" + EOL + "(prefix: string): string {" + EOL + "  return prefix + \"_\"";
  const iAfter = c.indexOf(afterHelpers, iBroken);
  if (iAfter >= 0) {
    // Extract the helpers that were inserted
    const helpersStart = "const kmPixelWidth = ref(1)";
    const helpersEnd = "})" + EOL + "}(prefix: string): string {";
    const iHelpers = c.indexOf(helpersStart, iBroken);
    const iHelpersEnd = c.indexOf(helpersEnd, iHelpers) + helpersEnd.length - "(prefix: string): string {".length;
    
    const helpersCode = c.substring(iHelpers, iHelpersEnd);
    console.log("Found helpers, length: " + helpersCode.length);
    
    // Remove helpers from current position
    const beforeHelpers = c.substring(0, iHelpers);
    const afterHelpersClean = c.substring(iHelpersEnd);
    c = beforeHelpers + afterHelpersClean;
    
    // Insert helpers BEFORE "function controlId"
    const controlIdMarker = "function controlId";
    const iControlId = c.indexOf(controlIdMarker);
    if (iControlId >= 0) {
      c = c.substring(0, iControlId) + helpersCode + EOL + c.substring(iControlId);
      console.log("Moved helpers before controlId");
    }
    
    // Also remove any duplicate "getDpadKeyStyle" function (the one with TypeScript types at line 1104)
    // Find the second occurrence
    const secondGetDpad = c.indexOf("function getDpadKeyStyle(dpad: any, dir: string): Record<string, string> {", c.indexOf("function controlId") + 100);
    if (secondGetDpad >= 0) {
      // Find its closing brace and remove the whole function
      let braceCount = 0;
      let foundBrace = false;
      let end2 = secondGetDpad;
      for (let j = secondGetDpad; j < c.length; j++) {
        if (c[j] === "{") { braceCount++; foundBrace = true; }
        else if (c[j] === "}") { braceCount--; }
        if (foundBrace && braceCount === 0) { end2 = j + 1; break; }
      }
      const duplicateFn = c.substring(secondGetDpad, end2);
      // Remove any blank lines after it too
      let end3 = end2;
      while (end3 < c.length && (c[end3] === EOL[0] || c[end3] === EOL[1])) end3++;
      c = c.substring(0, secondGetDpad) + c.substring(end3);
      console.log("Removed duplicate getDpadKeyStyle (" + duplicateFn.length + " bytes)");
    }
    
    fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
    console.log("Size: " + c.length);
  } else { console.log("FAIL: afterHelpers marker not found"); }
} else { console.log("FAIL: brokenMarker not found"); }
