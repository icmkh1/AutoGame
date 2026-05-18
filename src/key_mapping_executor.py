"""Key mapping executor that sends touch events via scrcpy control stream."""

from __future__ import annotations

import math


class KeyMappingExecutor:
    def __init__(self, scrcpy_manager):
        self.scrcpy = scrcpy_manager
        self._active_mapping = None
        self._enabled = False
        self._down_state_keys: dict[str, tuple[int, float, float]] = {}  # single-control key -> (pointer_id, x, y)
        self._dpad_states: dict[int, dict] = {}  # dpad index -> {pressed: set[str], pid: int|None, ex: float, ey: float}

    _DIR_VECTORS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    _OPPOSITE_DIRS = {"up": "down", "down": "up", "left": "right", "right": "left"}

    def apply(self, mapping_data):
        self._active_mapping = mapping_data
        self._enabled = True

    def remove(self):
        self.reset()
        self._active_mapping = None
        self._enabled = False

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

    @staticmethod
    def _resolve_edge(pressed_keys, key_to_dir, cx, cy, radius):
        """Resolve the edge position from a set of pressed dpad keys."""
        if not pressed_keys:
            return None
        dx = sum(KeyMappingExecutor._DIR_VECTORS[key_to_dir[k]][0] for k in pressed_keys if k in key_to_dir)
        dy = sum(KeyMappingExecutor._DIR_VECTORS[key_to_dir[k]][1] for k in pressed_keys if k in key_to_dir)
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return None
        return (cx + dx / length * radius, cy + dy / length * radius)

    def on_key_down(self, key_name):
        """Handle key press - send touch events at control positions."""
        if not self._enabled or not self._active_mapping:
            return False

        if key_name in self._down_state_keys:
            return False

        # Check single controls
        for ctrl in self._active_mapping.get("controls", []):
            if ctrl.get("key") == key_name:
                x = ctrl.get("x", 0.5)
                y = ctrl.get("y", 0.5)
                resp = self.scrcpy.send_normalized_touch(0, x, y)
                if resp.get("ok"):
                    pid = resp.get("pointer_id")
                    if pid is not None:
                        self._down_state_keys[key_name] = (pid, x, y)
                return True

        # Check swipes
        for swp in self._active_mapping.get("swipes", []):
            if swp.get("key") == key_name:
                path = swp.get("path", [])
                if path:
                    self.scrcpy.key_mapping_swipe(path)
                return True

        # Check dpad
        for dpad_idx, dpad in enumerate(self._active_mapping.get("dpad", [])):
            keys_config = dpad.get("keys", {})

            # Build key -> dir_name and dir_name -> key lookups
            key_to_dir = {}
            dir_to_key = {}
            for dir_name, info in keys_config.items():
                k = info.get("key")
                if k:
                    key_to_dir[k] = dir_name
                    dir_to_key[dir_name] = k

            if key_name not in key_to_dir:
                continue

            cx = dpad.get("x", 0.5)
            cy = dpad.get("y", 0.5)
            radius = dpad.get("size", 0.06)  # full radius to circle edge

            # Initialize state for this dpad
            if dpad_idx not in self._dpad_states:
                self._dpad_states[dpad_idx] = {"pressed": set(), "pid": None, "ex": 0.0, "ey": 0.0}

            state = self._dpad_states[dpad_idx]

            # Ignore duplicate press
            if key_name in state["pressed"]:
                return True

            old_pressed = set(state["pressed"])

            # Handle opposite-direction replacement
            new_dir_name = key_to_dir[key_name]
            opposite_dir = self._OPPOSITE_DIRS.get(new_dir_name)
            to_remove = None
            if opposite_dir and opposite_dir in dir_to_key:
                opp_key = dir_to_key[opposite_dir]
                if opp_key in old_pressed:
                    to_remove = opp_key

            # Compute old edge position
            old_edge = self._resolve_edge(old_pressed, key_to_dir, cx, cy, radius)

            # Build new pressed set
            new_pressed = set(old_pressed)
            if to_remove:
                new_pressed.discard(to_remove)
            new_pressed.add(key_name)
            state["pressed"] = new_pressed

            new_edge = self._resolve_edge(new_pressed, key_to_dir, cx, cy, radius)

            if new_edge is None:
                # All directions canceled out — release
                if state["pid"] is not None:
                    self.scrcpy.send_normalized_touch(1, state["ex"], state["ey"], pointer_id=state["pid"])
                    state["pid"] = None
                return True

            if old_edge is None:
                # No previous touch — start fresh from center
                resp = self.scrcpy.send_normalized_touch(0, cx, cy)
                if resp.get("ok"):
                    pid = resp.get("pointer_id")
                    if pid is not None:
                        self.scrcpy.send_normalized_touch(2, new_edge[0], new_edge[1], pointer_id=pid)
                        state["pid"] = pid
                        state["ex"], state["ey"] = new_edge
                return True

            # Both old and new exist → decide restart or move
            ox, oy = old_edge
            nx, ny = new_edge
            old_len = math.sqrt((ox - cx) ** 2 + (oy - cy) ** 2)
            new_len = math.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
            if old_len > 0 and new_len > 0:
                dot = ((ox - cx) / old_len) * ((nx - cx) / new_len) + ((oy - cy) / old_len) * ((ny - cy) / new_len)
            else:
                dot = 1.0

            if dot < 0:
                # Opposite direction → restart touch at center
                self.scrcpy.send_normalized_touch(1, state["ex"], state["ey"], pointer_id=state["pid"])
                resp = self.scrcpy.send_normalized_touch(0, cx, cy)
                if resp.get("ok"):
                    pid = resp.get("pointer_id")
                    if pid is not None:
                        self.scrcpy.send_normalized_touch(2, nx, ny, pointer_id=pid)
                        state["pid"] = pid
                        state["ex"], state["ey"] = nx, ny
            else:
                # Same general direction → just move touch
                self.scrcpy.send_normalized_touch(2, nx, ny, pointer_id=state["pid"])
                state["ex"], state["ey"] = nx, ny

            return True

        return False

    def on_key_up(self, key_name):
        """Handle key release - send touch up at control position."""
        if not self._enabled or not self._active_mapping:
            return False

        # Check single controls
        item = self._down_state_keys.pop(key_name, None)
        if item is not None:
            pid, px, py = item
            self.scrcpy.send_normalized_touch(1, px, py, pointer_id=pid)
            return True

        # Check dpad
        for dpad_idx, dpad in enumerate(self._active_mapping.get("dpad", [])):
            keys_config = dpad.get("keys", {})

            key_to_dir = {}
            for dir_name, info in keys_config.items():
                k = info.get("key")
                if k:
                    key_to_dir[k] = dir_name

            if key_name not in key_to_dir:
                continue

            if dpad_idx not in self._dpad_states:
                return True

            state = self._dpad_states[dpad_idx]
            state["pressed"].discard(key_name)

            if not state["pressed"]:
                # No more keys — release touch
                if state["pid"] is not None:
                    self.scrcpy.send_normalized_touch(1, state["ex"], state["ey"], pointer_id=state["pid"])
                    state["pid"] = None
            else:
                # Update touch to new edge position
                cx = dpad.get("x", 0.5)
                cy = dpad.get("y", 0.5)
                radius = dpad.get("size", 0.06)
                new_edge = self._resolve_edge(state["pressed"], key_to_dir, cx, cy, radius)
                if new_edge is not None and state["pid"] is not None:
                    self.scrcpy.send_normalized_touch(2, new_edge[0], new_edge[1], pointer_id=state["pid"])
                    state["ex"], state["ey"] = new_edge

            return True

        return False

    def reset(self):
        """Reset all active key states and release pointers."""
        self._down_state_keys.clear()
        self._dpad_states.clear()
        if self.scrcpy:
            self.scrcpy.key_mapping_reset()
