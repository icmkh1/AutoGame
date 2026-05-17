const fs = require("fs");
const path = "E:\\备份\\project\\Python\\AutoGame\\src\\api.py";
let c = fs.readFileSync(path, "utf-8");

// Add scrcpy_send_normalized_touch before key_mapping_trigger
const marker1 = "    def key_mapping_trigger";
const insert1 = "    def scrcpy_send_normalized_touch(self, action, x, y):\r\n" +
"        return self.scrcpy.send_normalized_touch(action, x, y)\r\n" +
"\r\n" +
"    def set_key_mapping_executor(self, executor):\r\n" +
"        self.key_mapping_executor = executor\r\n" +
"        return {\"ok\": True}\r\n" +
"\r\n" +
"    def exec_key_mapping_down(self, key_name):\r\n" +
"        if hasattr(self, 'key_mapping_executor') and self.key_mapping_executor:\r\n" +
"            return {\"ok\": self.key_mapping_executor.on_key_down(key_name)}\r\n" +
"        return {\"ok\": False, \"error\": \"executor not initialized\"}\r\n" +
"\r\n" +
"    def exec_key_mapping_up(self, key_name):\r\n" +
"        if hasattr(self, 'key_mapping_executor') and self.key_mapping_executor:\r\n" +
"            return {\"ok\": self.key_mapping_executor.on_key_up(key_name)}\r\n" +
"        return {\"ok\": False, \"error\": \"executor not initialized\"}\r\n" +
"\r\n" +
"    def get_key_mapping_mapped_keys(self):\r\n" +
"        if hasattr(self, 'key_mapping_executor') and self.key_mapping_executor:\r\n" +
"            return list(self.key_mapping_executor.get_mapped_keys())\r\n" +
"        return []\r\n" +
"\r\n";

const i1 = c.indexOf(marker1);
if (i1 >= 0) {
  c = c.substring(0, i1) + insert1 + c.substring(i1);
  console.log("Added API methods");
} else { console.log("FAIL: marker1 not found"); }

// Add to __dir__
const dirMarker = "'set_key_mapping_auto_hide',";
const newDir = "'set_key_mapping_auto_hide',\r\n" +
"            'scrcpy_send_normalized_touch',\r\n" +
"            'set_key_mapping_executor',\r\n" +
"            'exec_key_mapping_down',\r\n" +
"            'exec_key_mapping_up',\r\n" +
"            'get_key_mapping_mapped_keys',";

const i2 = c.indexOf(dirMarker);
if (i2 >= 0) {
  c = c.substring(0, i2) + newDir + c.substring(i2 + dirMarker.length);
  console.log("Updated __dir__");
} else { console.log("FAIL: dirMarker not found"); }

// Add key_mapping_executor in __init__
const initMarker = "self.key_mapping_hook = None";
const newInit = "self.key_mapping_hook = None\r\n        self.key_mapping_executor = None";
const i3 = c.indexOf(initMarker);
if (i3 >= 0) {
  c = c.substring(0, i3) + newInit + c.substring(i3 + initMarker.length);
  console.log("Added executor init");
} else { console.log("FAIL: initMarker not found"); }

fs.writeFileSync(path, c, "utf-8");
console.log("Done");
