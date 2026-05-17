import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_main.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "self.key_mapping_hook.set_window(self.window)",
    "self.key_mapping_hook.set_window(self.window)\r\n        self.api.set_key_mapping_hook(self.key_mapping_hook)"
)

with open("temp_main.py", "w", encoding="utf-8") as f:
    f.write(content)
print(f"OK: {len(content)}")
