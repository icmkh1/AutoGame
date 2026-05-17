import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_fm.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the corrupted line 383
content = content.replace(
    "f'{file_name}.json'J        try:",
    "f'{file_name}.json'\r\n        try:"
)

# Also ensure the method before it has proper spacing
# Check the get_key_mapping_files function

with open("temp_fm.py", "w", encoding="utf-8") as f:
    f.write(content)

# Verify it compiles
import py_compile
try:
    py_compile.compile("temp_fm.py", doraise=True)
    print("COMPILE OK")
except py_compile.PyCompileError as e:
    print(f"COMPILE FAIL: {e}")

print(f"Size: {len(content)}")
