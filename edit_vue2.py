import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_fix.vue", "r", encoding="utf-8") as f:
    content = f.read()

# Add remove_key_mapping to stopConnection
old = "async function stopConnection() {\n  stopPolling()\n  closeDecoders()"
new = "async function stopConnection() {\n  try { await callApi(\"remove_key_mapping\") } catch {}\n  stopPolling()\n  closeDecoders()"
content = content.replace(old, new)

# Remove unused watch import
content = content.replace(", watch, type Ref", ", type Ref")

with open("temp_fix.vue", "w", encoding="utf-8") as f:
    f.write(content)

print(f"OK: {len(content)}")
