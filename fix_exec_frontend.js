const fs = require("fs");
let c = fs.readFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", "utf-8");
const EOL = "\r\n";

// Update execKeyDown to also call backend executor
const execFn = "function execKeyDown(key) {" + EOL +
  "  const mapped = findControlByKey(key)" + EOL +
  "  if (!mapped || !session.value.width || !session.value.height) return" + EOL +
  "  const sw = session.value.width" + EOL +
  "  const sh = session.value.height" + EOL +
  "  if (mapped.kind === \"single\") {" + EOL +
  "    const sx = Math.round(mapped.x * sw)" + EOL +
  "    const sy = Math.round(mapped.y * sh)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 0, sx, sy, sw, sh).catch(() => {})" + EOL +
  "  } else if (mapped.kind === \"dpad\") {" + EOL +
  "    const sx = Math.round(mapped.x * sw)" + EOL +
  "    const sy = Math.round(mapped.y * sh)" + EOL +
  "    const dirOffsets = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }" + EOL +
  "    const [dx, dy] = dirOffsets[mapped.dir] || [0, 0]" + EOL +
  "    const dist = mapped.size * sw * 0.4" + EOL +
  "    const ex = Math.round(sx + dx * dist)" + EOL +
  "    const ey = Math.round(sy + dy * dist)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 0, sx, sy, sw, sh).catch(() => {})" + EOL +
  "    callApi(\"scrcpy_send_touch\", 2, ex, ey, sw, sh).catch(() => {})" + EOL +
  "    callApi(\"scrcpy_send_touch\", 1, ex, ey, sw, sh).catch(() => {})" + EOL +
  "  } else if (mapped.kind === \"swipe\" && mapped.path && mapped.path.length > 1) {" + EOL +
  "    const pathPx = mapped.path.map(p => ({" + EOL +
  "      x: Math.round(p.x * sw)," + EOL +
  "      y: Math.round(p.y * sh)," + EOL +
  "      delayMs: p.delayMs" + EOL +
  "    }))" + EOL +
  "    callApi(\"key_mapping_swipe\", pathPx).catch(() => {})" + EOL +
  "  }" + EOL +
  "}";

// Add also notify executor after the call
const execUpdate = execFn.substring(0, execFn.length - 1) + "  // Also notify backend executor" + EOL +
  "  callApi(\"exec_key_mapping_down\", key).catch(() => {})" + EOL +
  "}";

if (c.indexOf(execFn) >= 0) {
  c = c.replace(execFn, execUpdate);
  console.log("Updated execKeyDown");
} else {
  console.log("FAIL: execKeyDown not found");
  // Try to find partial match
  const i = c.indexOf("function execKeyDown(key");
  if (i >= 0) {
    console.log("Found at", i);
    console.log(c.substring(i, i+200).replace(/\r/g,"\\r").replace(/\n/g,"\\n"));
  }
}

// Update execKeyUp to also call backend executor
const execUpFn = "function execKeyUp(key) {" + EOL +
  "  const mapped = findControlByKey(key)" + EOL +
  "  if (!mapped || !session.value.width || !session.value.height) return" + EOL +
  "  const sw = session.value.width" + EOL +
  "  const sh = session.value.height" + EOL +
  "  if (mapped.kind === \"single\") {" + EOL +
  "    const sx = Math.round(mapped.x * sw)" + EOL +
  "    const sy = Math.round(mapped.y * sh)" + EOL +
  "    callApi(\"scrcpy_send_touch\", 1, sx, sy, sw, sh).catch(() => {})" + EOL +
  "  }" + EOL +
  "}";
const execUpUpdate = execUpFn.substring(0, execUpFn.length - 1) + "  // Also notify backend executor" + EOL +
  "  callApi(\"exec_key_mapping_up\", key).catch(() => {})" + EOL +
  "}";

if (c.indexOf(execUpFn) >= 0) {
  c = c.replace(execUpFn, execUpUpdate);
  console.log("Updated execKeyUp");
} else {
  console.log("FAIL: execKeyUp not found");
}

fs.writeFileSync("E:\\备份\\project\\Python\\AutoGame\\frontend\\src\\components\\ScreenCastView.vue", c, "utf-8");
console.log("Done");
