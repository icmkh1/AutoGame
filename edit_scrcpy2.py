import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("temp_scrcpy_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

append = '''

    # Key mapping: send events via scrcpy control stream

    def apply_key_mapping(self, mapping_data: dict) -> dict:
        self._active_key_mapping = mapping_data
        return {"ok": True}

    def remove_key_mapping(self) -> dict:
        self._active_key_mapping = None
        return {"ok": True}

    def key_mapping_trigger(self, key_name: str, action: str) -> dict:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        if action == "down":
            android_action = self.ANDROID_ACTION_DOWN
        elif action == "up":
            android_action = self.ANDROID_ACTION_UP
        else:
            return {"ok": False, "error": f"unknown action: {action}"}
        android_keycode = self.ANDROID_KEYCODE_MAP.get(key_name)
        if android_keycode is not None:
            self._submit(self._client.control.send_keycode(android_action, android_keycode))
            return {"ok": True}
        return {"ok": False, "error": f"unknown key: {key_name}"}

    def key_mapping_swipe(self, path_data: list) -> dict:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        if not self._last_session:
            return {"ok": False, "error": "no session size"}
        try:
            sw, sh = self._last_session
            self._submit(self._send_swipe_async(path_data, sw, sh))
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _send_swipe_async(self, path_data: list, sw: int, sh: int):
        if not path_data:
            return
        first = path_data[0]
        await self._client.control.send_touch(0, first["x"], first["y"], sw, sh)
        for i in range(1, len(path_data)):
            pt = path_data[i]
            delay = pt.get("delayMs", 0) - path_data[i-1].get("delayMs", 0)
            if delay > 0:
                await asyncio.sleep(delay / 1000.0)
            await self._client.control.send_touch(2, pt["x"], pt["y"], sw, sh)
        last = path_data[-1]
        await self._client.control.send_touch(1, last["x"], last["y"], sw, sh)
'''

content = content + append
with open("temp_scrcpy_manager.py", "w", encoding="utf-8") as f:
    f.write(content)
print(f"OK: {len(content)}")
