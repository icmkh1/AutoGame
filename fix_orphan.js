const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Find the orphan braces after "// DPad resize moved"
const orphanBlock = "  // DPad resize moved to onResizeMouseMove" + EOL +
  "  // (handled by document-level listeners)" + EOL +
  "  }" + EOL +
  "}";

// Check what the proper closure should be
// The function onOverlayMouseMove should end with just the dragTarget cleanup
// Looking at the code: last real content before orphan is:
//     dragTarget.y = Math.max(0, Math.min(1, norm.y - dragOffsetY))
//   }
// Then orphan braces: ]

const i = c.indexOf(orphanBlock);
if (i >= 0) {
  // Replace with just the comment (no orphan braces)
  const replacement = "  // DPad resize moved to onResizeMouseMove (document-level)";
  c = c.substring(0, i) + replacement + c.substring(i + orphanBlock.length);
  console.log("Removed orphan braces");
} else {
  console.log("FAIL: orphanBlock not found");
  // Try alternative pattern
  const altOrphan = "  // DPad resize moved to onResizeMouseMove" + EOL +
    "  // (handled by document-level listeners)" + EOL +
    "  }";
  const i2 = c.indexOf(altOrphan);
  if (i2 >= 0) {
    // Find where the extra braces end
    let j = i2 + altOrphan.length;
    while (j < c.length && (c[j] === " " || c[j] === "}" || c[j] === EOL[0] || c[j] === EOL[1])) j++;
    // Find the proper function-level close by looking for function keyword
    const restAfter = c.substring(j);
    // Remove the extra braces - keep only up to the comment
    const newBlock = "  // DPad resize moved to onResizeMouseMove (document-level)" + EOL;
    c = c.substring(0, i2) + newBlock + restAfter;
    console.log("Removed orphan braces (alt)");
  }
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Size: " + c.length);
