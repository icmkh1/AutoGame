with open("temp_vue_fix.vue","r",encoding="utf-8")as f:c=f.read()
# Fix 1: dpad width/height
c=c.replace(':style="{ left: dpad.x + chr(39) + "px" + chr(39) + ", top: dpad.y + chr(39) + "px" + chr(39) + " }">',':style="{ left: dpad.x + chr(39) + "px" + chr(39) + ", top: dpad.y + chr(39) + "px" + chr(39) + ", width: dpad.size + chr(39) + "px" + chr(39) + ", height: dpad.size + chr(39) + "px" + chr(39) + " }" @mousedown.left.stop="startDrag($event,dpad,chr(39)+dpad+chr(39))">')
print(len(c))
