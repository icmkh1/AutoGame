"""Key mapping executor that sends touch events via scrcpy control stream."""

from __future__ import annotations

import math
import random


class KeyMappingExecutor:
    def __init__(self, scrcpy_manager):
        self.scrcpy = scrcpy_manager
        self._active_mapping = None
        self._enabled = False
        self._enabled_before_focus = False
        self._down_state_keys: dict[str, tuple[int, float, float]] = {}  # single-control key -> (pointer_id, x, y)
        self._dpad_states: dict[int, dict] = {}  # dpad index -> {pressed: set[str], pid: int|None, ex: float, ey: float}
        self._active_swipe_keys: set[str] = set()  # pressed swipe keys (dedup + re-apply on release)

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
                offset_range = ctrl.get("offsetRange", 0) / 100.0
                if offset_range > 0:
                    x += (random.random() * 2 - 1) * offset_range
                    y += (random.random() * 2 - 1) * offset_range
                    x = max(0.0, min(1.0, x))
                    y = max(0.0, min(1.0, y))
                resp = self.scrcpy.send_normalized_touch(0, x, y)
                if resp.get("ok"):
                    pid = resp.get("pointer_id")
                    if pid is not None:
                        self._down_state_keys[key_name] = (pid, x, y)
                return True

        # Check swipes
        if key_name in self._active_swipe_keys:
            return True  # swipe already in progress, skip key repeat
        for swp in self._active_mapping.get("swipes", []):
            if swp.get("key") == key_name:
                path = swp.get("path", [])
                if path:
                    self._active_swipe_keys.add(key_name)
                    recreate = self._capture_active_touches()
                    self.scrcpy.key_mapping_swipe(path, recreate_touches=recreate)
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
                offset_range = dpad.get("offsetRange", 0) / 100.0
                ox = (random.random() * 2 - 1) * offset_range if offset_range > 0 else 0.0
                oy = (random.random() * 2 - 1) * offset_range if offset_range > 0 else 0.0
                self._dpad_states[dpad_idx] = {"pressed": set(), "pid": None, "ex": 0.0, "ey": 0.0, "ox": ox, "oy": oy}

            state = self._dpad_states[dpad_idx]

            # Apply stored random offset
            cx += state["ox"]
            cy += state["oy"]

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

        # Check swipe keys: update state with re-created touch pointers
        if key_name in self._active_swipe_keys:
            self._active_swipe_keys.discard(key_name)
            results = self.scrcpy.wait_swipe_complete(timeout=0.5)
            if results:
                self._apply_recreate_results(results)
            return True

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
                cx = dpad.get("x", 0.5) + state.get("ox", 0.0)
                cy = dpad.get("y", 0.5) + state.get("oy", 0.0)
                radius = dpad.get("size", 0.06)
                new_edge = self._resolve_edge(state["pressed"], key_to_dir, cx, cy, radius)
                if new_edge is not None and state["pid"] is not None:
                    self.scrcpy.send_normalized_touch(2, new_edge[0], new_edge[1], pointer_id=state["pid"])
                    state["ex"], state["ey"] = new_edge

            return True

        return False

    # Keys that should be re-created after a swipe (movement/direction keys).
    # Only these keys get the UP→delay→DOWN refresh; other keys are left alone.
    _DIRECTION_KEYS = {"A", "D", "a", "d"}

    def _capture_active_touches(self) -> list:
        """Snapshot active direction-key touches before swipe, for later re-creation.

        Only captures keys listed in _DIRECTION_KEYS — other active controls
        are not touched by the swipe refresh.
        """
        touches = []
        for key_name, (pid, x, y) in self._down_state_keys.items():
            if key_name in self._DIRECTION_KEYS:
                touches.append({"type": "control", "key": key_name, "old_pid": pid, "x": x, "y": y})
        for dpad_idx, state in self._dpad_states.items():
            if state["pid"] is not None and state["pressed"]:
                dpads = self._active_mapping.get("dpad", [])
                if dpad_idx < len(dpads):
                    dpad = dpads[dpad_idx]
                    cx = dpad.get("x", 0.5) + state.get("ox", 0.0)
                    cy = dpad.get("y", 0.5) + state.get("oy", 0.0)
                    touches.append({
                        "type": "dpad", "idx": dpad_idx, "old_pid": state["pid"],
                        "cx": cx, "cy": cy, "ex": state["ex"], "ey": state["ey"],
                    })
        return touches

    def _apply_recreate_results(self, results: list):
        """Update touch state with new pointer IDs after swipe re-creation."""
        for r in results:
            if r["type"] == "control":
                key = r["key"]
                if key in self._down_state_keys:
                    _pid, x, y = self._down_state_keys[key]
                    self._down_state_keys[key] = (r["new_pid"], x, y)
            elif r["type"] == "dpad":
                idx = r["idx"]
                if idx in self._dpad_states:
                    self._dpad_states[idx]["pid"] = r["new_pid"]

    def is_key_down(self, key_name: str) -> bool:
        """Check if a key is currently held down (active touch pointer exists)."""
        return key_name in self._down_state_keys

    def execute_screen_swipe(self, key_name: str, direction: str,
                              distance: float, duration_ms: float,
                              position_offset: float = 0.0,
                              duration_offset: float = 0.0) -> dict:
        """Execute a swipe using an active direction key's touch pointer.

        The touch pointer stays DOWN — no UP is sent. This simulates a finger
        sliding on screen while already holding a direction, as in the 瞬侧 technique.

        Returns:
            dict with 'ok' and optional 'error'
        """
        item = self._down_state_keys.get(key_name)
        if item is None:
            return {"ok": False, "error": f"方向键 {key_name} 未按下"}

        pid, start_x, start_y = item

        if position_offset > 0:
            start_x += (random.random() * 2 - 1) * position_offset
            start_y += (random.random() * 2 - 1) * position_offset
            start_x = max(0.0, min(1.0, start_x))
            start_y = max(0.0, min(1.0, start_y))

        if duration_offset > 0:
            duration_ms += (random.random() * 2 - 1) * duration_offset
            duration_ms = max(10.0, duration_ms)

        dir_map = {'左': (-1, 0), '右': (1, 0)}
        dx, dy = dir_map.get(direction, (0, 0))

        target_x = max(0.0, min(1.0, start_x + dx * distance))
        target_y = max(0.0, min(1.0, start_y + dy * distance))

        result = self.scrcpy.execute_direction_swipe(
            pid, start_x, start_y, target_x, target_y, duration_ms
        )

        if result.get("ok"):
            self._down_state_keys[key_name] = (pid, result.get("final_x", target_x), result.get("final_y", target_y))

        return result

    def reset(self):
        """Reset all active key states and release pointers."""
        self._down_state_keys.clear()
        self._dpad_states.clear()
        self._active_swipe_keys.clear()
        if self.scrcpy:
            self.scrcpy.key_mapping_reset()

    def set_focus_state(self, focused):
        if not focused and self._enabled:
            self._enabled_before_focus = self._enabled
            self._enabled = False
            self.reset()
        elif focused and not self._enabled and self._enabled_before_focus:
            self._enabled = True
