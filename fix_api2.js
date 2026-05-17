const fs = require("fs");
const path = "E:\\备份\\project\\Python\\AutoGame\\src\\api.py";
let c = fs.readFileSync(path, "utf-8");

// Add import for KeyMappingExecutor
const importMarker = "from .scrcpy_manager import ScrcpyManager";
const newImport = importMarker + "\r\nfrom .key_mapping_executor import KeyMappingExecutor";
c = c.replace(importMarker, newImport);

// Add executor init after scrcpy init
const scrcpyInit = "self.scrcpy = ScrcpyManager()";
const executorInit = scrcpyInit + "\r\n        self.key_mapping_executor = KeyMappingExecutor(self.scrcpy)";
c = c.replace(scrcpyInit, executorInit);

// Update apply_key_mapping to also use executor
const applyFn = "def apply_key_mapping(self, file_name):\r\n" +
"        data = self.file_manager.load_key_mapping_file(file_name)\r\n" +
"        if not data:\r\n" +
"            return {\"ok\": False, \"error\": \"failed to load key mapping\"}\r\n" +
"        return self.scrcpy.apply_key_mapping(data)";
const newApplyFn = "def apply_key_mapping(self, file_name):\r\n" +
"        data = self.file_manager.load_key_mapping_file(file_name)\r\n" +
"        if not data:\r\n" +
"            return {\"ok\": False, \"error\": \"failed to load key mapping\"}\r\n" +
"        self.scrcpy.apply_key_mapping(data)\r\n" +
"        if self.key_mapping_executor:\r\n" +
"            self.key_mapping_executor.apply(data)\r\n" +
"        return {\"ok\": True}";

if (c.indexOf(applyFn) >= 0) {
  c = c.replace(applyFn, newApplyFn);
  console.log("Updated apply_key_mapping");
} else { console.log("FAIL: applyFn not found"); }

// Update remove_key_mapping
const removeFn = "def remove_key_mapping(self):\r\n" +
"        return self.scrcpy.remove_key_mapping()";
const newRemoveFn = "def remove_key_mapping(self):\r\n" +
"        self.scrcpy.remove_key_mapping()\r\n" +
"        if self.key_mapping_executor:\r\n" +
"            self.key_mapping_executor.remove()\r\n" +
"        return {\"ok\": True}";
if (c.indexOf(removeFn) >= 0) {
  c = c.replace(removeFn, newRemoveFn);
  console.log("Updated remove_key_mapping");
} else { console.log("FAIL: removeFn not found"); }

// Remove the old set_key_mapping_executor API method since it's now auto-initialized
// Actually keep it for backwards compatibility, but also auto-init

fs.writeFileSync(path, c, "utf-8");
console.log("Done");
