import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_api.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add key_mapping_hook reference in __init__
content = content.replace(
    "self.scrcpy = ScrcpyManager()",
    "self.scrcpy = ScrcpyManager()\r\n        self.key_mapping_hook = None"
)

# Add set_key_mapping_hook method before __dir__
hook_method = '''
    def set_key_mapping_hook(self, hook):
        self.key_mapping_hook = hook

    def set_key_mapping_auto_hide(self, enabled: bool):
        if self.key_mapping_hook is None:
            return {"ok": False, "error": "hook not initialized"}
        if enabled:
            self.key_mapping_hook.start()
        else:
            self.key_mapping_hook.stop()
        return {"ok": True}
'''

idx = content.find("    def __dir__(self):")
if idx >= 0:
    content = content[:idx] + hook_method + content[idx:]

# Update __dir__
old = "'get_android_keycode',"
new = "'get_android_keycode',\r\n            'set_key_mapping_auto_hide',"
content = content.replace(old, new)

with open("temp_api.py", "w", encoding="utf-8") as f:
    f.write(content)
print(f"OK: {len(content)}")
