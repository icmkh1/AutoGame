const fs = require("fs");
const path = "E:\\备份\\project\\Python\\AutoGame\\src\\scrcpy_manager.py";
let c = fs.readFileSync(path, "utf-8");

// Add send_normalized_touch method before key_mapping_swipe
const marker = "    def key_mapping_swipe";
const insert = "    def send_normalized_touch(self, action: int, x: float, y: float) -> dict:\r\n" +
"        \"\"\"Send touch event with normalized 0.0-1.0 coordinates.\r\n" +
"        Converts to session pixel coordinates using last known session size.\r\n" +
"        \"\"\"\r\n" +
"        if self._client is None or self._client.control is None:\r\n" +
"            return {\"ok\": False, \"error\": \"control stream is not running\"}\r\n" +
"        if not self._last_session:\r\n" +
"            return {\"ok\": False, \"error\": \"no session size\"}\r\n" +
"        sw, sh = self._last_session\r\n" +
"        px = max(0, min(sw, int(x * sw)))\r\n" +
"        py = max(0, min(sh, int(y * sh)))\r\n" +
"        return self._submit(self._send_touch(action, px, py, sw, sh))\r\n" +
"\r\n" +
"\r\n";

const idx = c.indexOf(marker);
if (idx >= 0) {
  c = c.substring(0, idx) + insert + c.substring(idx);
  fs.writeFileSync(path, c, "utf-8");
  console.log("Added send_normalized_touch to scrcpy_manager.py");
} else {
  console.log("FAIL: marker not found");
}
