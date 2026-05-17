import os, sys

# Update key_mapping_executor.py to send touch events instead of keycodes
path = r"E:\备份\project\Python\AutoGame\src\key_mapping_executor.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_content = r'''"""Key mapping executor that sends touch events via scrcpy control stream."""

from __future__ import annotations

from typing import Any

class KeyMappingExecutor:
    def __init__(self, scrcpy_manager):
        self.scrcpy = scrcpy_manager
        self._active_mapping = None
        self._enabled = False
        self._pressed_keys = set()

    def apply(self, mapping_data):
        self._active_mapping = mapping_data
        self._enabled = True

    def remove(self):
        self._active_mapping = None
        self._enabled = False
        self._pressed_keys.clear()

    @property
    def enabled(self):
        return self._enabled and self._active_mapping is not None

    def get_mapped_keys(self):
        """Return set of all configured keys."""
        keys = set()
        if not self._active_mapping:
            return keys
        for ctrl in self._active_mapping.get("controls", []):
            k = ctrl.get("key")
            if k:
                keys.add(k)
        for swp in self._active_mapping.get("swipes", []):
            k = swp.get("key")
            if k:
                keys.add(k)
        for dpad in self._active_mapping.get("dpad", []):
            for _, info in dpad.get("keys", {}).items():
                k = info.get("key")
                if k:
                    keys.add(k)
        return keys

    def on_key_down(self, key_name):
        """Handle key press - send touch events at control positions."""
        if not self._enabled or not self._active_mapping:
            return False
        if key_name in self._pressed_keys:
            return False
        self._pressed_keys.add(key_name)

        # Check single controls
        for ctrl in self._active_mapping.get("controls", []):
            if ctrl.get("key") == key_name:
                x = ctrl.get("x", 0.5)
                y = ctrl.get("y", 0.5)
                self.scrcpy.send_normalized_touch(0, x, y)
                return True

        # Check swipes
        for swp in self._active_mapping.get("swipes", []):
            if swp.get("key") == key_name:
                path = swp.get("path", [])
                if path:
                    self.scrcpy.key_mapping_swipe(path)
                return True

        # Check dpad
        for dpad in self._active_mapping.get("dpad", []):
            for dir_name, info in dpad.get("keys", {}).items():
                if info.get("key") == key_name:
                    cx = dpad.get("x", 0.5)
                    cy = dpad.get("y", 0.5)
                    size_norm = dpad.get("size", 0.06)
                    dir_offsets = {"up": [0, -1], "down": [0, 1], "left": [-1, 0], "right": [1, 0]}
                    dx, dy = dir_offsets.get(dir_name, [0, 0])
                    dist = size_norm * 0.4
                    ex = cx + dx * dist
                    ey = cy + dy * dist
                    self.scrcpy.send_normalized_touch(0, cx, cy)
                    self.scrcpy.send_normalized_touch(2, ex, ey)
                    self.scrcpy.send_normalized_touch(1, ex, ey)
                    return True

        return False

    def on_key_up(self, key_name):
        """Handle key release - send touch up at control position."""
        if not self._enabled or not self._active_mapping:
            return False
        if key_name not in self._pressed_keys:
            return False
        self._pressed_keys.discard(key_name)

        # Single controls need touch up
        for ctrl in self._active_mapping.get("controls", []):
            if ctrl.get("key") == key_name:
                x = ctrl.get("x", 0.5)
                y = ctrl.get("y", 0.5)
                self.scrcpy.send_normalized_touch(1, x, y)
                return True

        return False
'''

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated key_mapping_executor.py")
