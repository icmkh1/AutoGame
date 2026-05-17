import os, subprocess, py_compile
os.chdir(os.path.dirname(os.path.abspath(__file__)))

result = subprocess.run(["git", "show", "HEAD:src/path_manager.py"], capture_output=True, text=True, encoding="utf-8")
content = result.stdout

old = "    @property\n    def config_path(self) -> Path:"
new = """    @property
    def key_mapping_dir(self) -> Path:
        return self.ensure_user_dir(r"data\\key_mapping")

    @property
    def config_path(self) -> Path:"""

content = content.replace(old, new, 1)

with open("src/path_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

try:
    py_compile.compile("src/path_manager.py", doraise=True)
    print("OK")
except py_compile.PyCompileError as e:
    print(f"FAIL: {e}")
