import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_api_fix.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the __dir__ method - add key mapping entries
old_dir_end = "'scrcpy_switch_app', 'scrcpy_home',\n        ]"
new_dir_end = """'scrcpy_switch_app', 'scrcpy_home',
            'get_key_mapping_files',
            'load_key_mapping_file',
            'save_key_mapping_file',
            'create_key_mapping_file',
            'rename_key_mapping_file',
            'delete_key_mapping_file',
            'apply_key_mapping',
            'remove_key_mapping',
            'key_mapping_trigger',
            'key_mapping_swipe',
            'get_android_keycode',
            'set_key_mapping_auto_hide',
        ]"""

content = content.replace(old_dir_end, new_dir_end)

with open("temp_api_fix.py", "w", encoding="utf-8") as f:
    f.write(content)

# Verify
import py_compile
try:
    py_compile.compile("temp_api_fix.py", doraise=True)
    print("COMPILE OK")
except py_compile.PyCompileError as e:
    print(f"COMPILE FAIL: {e}")

print(f"Size: {len(content)}")
