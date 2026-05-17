# -*- coding: utf-8 -*-
import re

with open("E:\\备份\\project\\Python\\AutoGame\\temp_f5.vue", "r", encoding="utf-8") as f:
    content = f.read()

print("=== Checking key patterns ===")
# Check toSessionCoords function
idx = content.find("function toSessionCoords")
if idx >= 0:
    print("toSessionCoords found at", idx)
    print(repr(content[idx:idx+500]))
else:
    print("toSessionCoords NOT FOUND")
    # Try to find the function differently
    idx2 = content.find("toSessionCoords")
    if idx2 >= 0:
        print("References to toSessionCoords at", idx2)
        print(repr(content[idx2-50:idx2+100]))

# Check startDrag
print("\n=== startDrag ===")
idx = content.find("function startDrag")
if idx >= 0:
    print("Found at", idx)
    print(repr(content[idx:idx+500]))
else:
    print("NOT FOUND")

# Check single control style
print("\n=== single style ===")
idx = content.find("key-control")
if idx >= 0:
    print("Found at", idx)
    print(repr(content[idx:idx+500]))
else:
    print("NOT FOUND")

# Check drag handling
print("\n=== drag handling ===")
idx = content.find("// Drag handling")
if idx >= 0:
    print("Found at", idx)
    print(repr(content[idx:idx+400]))
else:
    print("NOT FOUND")

# Check swipe create
print("\n=== swipe create ===")
idx = content.find('label: "滑动"')
if idx >= 0:
    print("Found at", idx)
    print(repr(content[idx-200:idx+200]))
else:
    print("NOT FOUND")

# Check startDpadResize
print("\n=== startDpadResize ===")
idx = content.find("function startDpadResize")
if idx >= 0:
    print("Found at", idx)
    print(repr(content[idx:idx+400]))
else:
    print("NOT FOUND")

# Check DPad resize in onOverlayMouseMove
print("\n=== resize in move ===")
idx = content.find("// DPad resize")
if idx >= 0:
    print("Found at", idx)
    print(repr(content[idx:idx+400]))
else:
    print("NOT FOUND")

# Check resize cleanup
print("\n=== resize cleanup ===")
idx = content.find("resizeTarget = null")
counter = 0
pos = 0
while counter < 3:
    idx = content.find("resizeTarget = null", pos)
    if idx < 0:
        break
    print(f"Found at {idx}")
    print(repr(content[max(0,idx-50):idx+50]))
    pos = idx + 1
    counter += 1

"'
