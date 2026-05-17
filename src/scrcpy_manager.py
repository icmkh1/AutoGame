from __future__ import annotations

import asyncio
import base64
import queue
import threading
from pathlib import Path
from typing import Any

from autoxkit.android import AudioVideoEvent, ScrcpyClient, ScrcpyOptions, StreamKind


class ScrcpyManager:
    """Manages a single scrcpy connection for screen casting.

    Runs the async scrcpy client on a background thread and exposes
    thread-safe synchronous methods for the pywebview API.
    """

    PLUGIN_DIR = Path(__file__).resolve().parents[1] / "plugins" / "scrcpy"

    ANDROID_KEYCODE_HOME = 3
    ANDROID_KEYCODE_BACK = 4
    ANDROID_KEYCODE_VOLUME_UP = 24
    ANDROID_KEYCODE_VOLUME_DOWN = 25
    ANDROID_KEYCODE_APP_SWITCH = 187
    ANDROID_ACTION_DOWN = 0
    ANDROID_ACTION_UP = 1

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="scrcpy-manager")
        self._thread.start()
        self._client: ScrcpyClient | None = None
        self._pump_task: asyncio.Task[None] | None = None
        self._events: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=480)
        self._last_session: tuple[int, int] | None = None

    # ------------------------------------------------------------------ #
    # Public API (called from pywebview thread)
    # ------------------------------------------------------------------ #

    def start(self, serial: str | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Start a scrcpy connection."""
        return self._submit(self._start(serial, config))

    def stop(self) -> dict[str, Any]:
        """Stop the scrcpy connection."""
        return self._submit(self._stop())

    def status(self) -> dict[str, Any]:
        """Return current connection status."""
        if self._client is None:
            return {"running": False}
        return {
            "running": True,
            "deviceName": self._client.device_meta.device_name if self._client.device_meta else None,
        }

    def poll_events(self, limit: int = 30) -> list[dict[str, Any]]:
        """Poll events from the internal queue."""
        items: list[dict[str, Any]] = []
        for _ in range(max(1, min(limit, 240))):
            try:
                items.append(self._events.get_nowait())
            except queue.Empty:
                break
        return items

    def send_touch(self, action: int, x: int, y: int, width: int, height: int) -> dict[str, Any]:
        return self._submit(self._send_touch(action, x, y, width, height))

    def send_keycode(self, keycode: int, action: int = 0) -> dict[str, Any]:
        return self._submit(self._send_keycode(action, keycode))

    def set_clipboard(self, text: str) -> dict[str, Any]:
        return self._submit(self._set_clipboard(text))

    def switch_to_wireless(self, serial: str | None = None) -> dict[str, Any]:
        return self._submit(self._switch_to_wireless(serial))

    def discover_usb_serial(self) -> str | None:
        return self._submit(self._discover_usb_serial())

    def volume_up(self) -> dict[str, Any]:
        return self._submit(self._volume_up())

    def volume_down(self) -> dict[str, Any]:
        return self._submit(self._volume_down())

    def back(self) -> dict[str, Any]:
        return self._submit(self._back())

    def switch_app(self) -> dict[str, Any]:
        return self._submit(self._switch_app())

    def home(self) -> dict[str, Any]:
        return self._submit(self._home())

    # ------------------------------------------------------------------ #
    # Async implementations
    # ------------------------------------------------------------------ #

    async def _start(self, serial: str | None, config: dict[str, Any] | None) -> dict[str, Any]:
        if self._client is not None:
            return self._make_status()

        cfg = config or {}
        video_source = cfg.get("videoSource", "display")
        audio_source = cfg.get("audioSource", "output")
        quality = cfg.get("quality", "unlimited")
        bitrate = cfg.get("bitrate", "unlimited")
        fps_limit = cfg.get("fpsLimit", "unlimited")

        video_enabled = video_source != "none"
        audio_enabled = audio_source != "none"

        server_args: list[str] = []
        if video_enabled:
            server_args.append(f"video_source={video_source}")
            if quality != "unlimited":
                server_args.append(f"max_size={quality}")
            if bitrate != "unlimited":
                # e.g. "4M" -> 4000000
                bitrate_int = bitrate[:-1] + "000000" if bitrate.endswith("M") else bitrate
                server_args.append(f"video_bit_rate={bitrate_int}")
            if fps_limit != "unlimited":
                server_args.append(f"max_fps={fps_limit}")
        if audio_enabled:
            server_args.append(f"audio_source={audio_source}")
            server_args.append("audio_codec=raw")
        server_args.append("video_codec=h264")

        adb_path = self.PLUGIN_DIR / "adb.exe"
        server_path = self.PLUGIN_DIR / "scrcpy-server"

        options = ScrcpyOptions(
            serial=serial,
            adb_path=adb_path,
            server_path=server_path,
            video=video_enabled,
            audio=audio_enabled,
            control=True,
            log_level="info",
            server_args=server_args,
        )

        client = ScrcpyClient(options)
        try:
            await client.start()
        except Exception as exc:
            return {"running": False, "error": str(exc)}

        self._client = client
        self._pump_task = asyncio.create_task(self._pump_events(client))
        return self._make_status()

    async def _stop(self) -> dict[str, Any]:
        if self._pump_task is not None:
            self._pump_task.cancel()
            self._pump_task = None
        if self._client is not None:
            await self._client.stop()
            self._client = None
        self._last_session = None
        self._clear_queue()
        return {"running": False}

    async def _send_touch(self, action: int, x: int, y: int, width: int, height: int) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_touch(action, x, y, width, height, pressure=0.0 if action == 1 else 1.0)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _send_keycode(self, action: int, keycode: int) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_keycode(action, keycode)
            if action == 0:
                await self._client.control.send_keycode(1, keycode)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _set_clipboard(self, text: str) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.set_clipboard(text, sequence=1, paste=False)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _switch_to_wireless(self, serial: str | None) -> dict[str, Any]:
        resolved = serial
        if not resolved:
            from autoxkit.android.adb import AdbServerLauncher
            launcher = AdbServerLauncher(
                adb_path=self.PLUGIN_DIR / "adb.exe",
                server_path=self.PLUGIN_DIR / "scrcpy-server",
            )
            resolved = await launcher.discover_usb_serial()
            if not resolved:
                return {"ok": False, "error": "could not find a single USB device; please enter the serial"}
        from autoxkit.android.adb import AdbServerLauncher
        launcher = AdbServerLauncher(
            adb_path=self.PLUGIN_DIR / "adb.exe",
            server_path=self.PLUGIN_DIR / "scrcpy-server",
            serial=resolved,
        )
        try:
            device_ip = await launcher.get_device_ip()
            await launcher.enable_tcpip(5555)
            await asyncio.sleep(1)
            address = f"{device_ip}:5555"
            await launcher.connect_tcpip(address)
            await asyncio.sleep(2)
            return {"ok": True, "serial": address}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    async def _discover_usb_serial(self) -> str | None:
        from autoxkit.android.adb import AdbServerLauncher
        launcher = AdbServerLauncher(
            adb_path=self.PLUGIN_DIR / "adb.exe",
            server_path=self.PLUGIN_DIR / "scrcpy-server",
        )
        return await launcher.discover_usb_serial()

    async def _volume_up(self) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_keycode(self.ANDROID_ACTION_DOWN, self.ANDROID_KEYCODE_VOLUME_UP)
            await self._client.control.send_keycode(self.ANDROID_ACTION_UP, self.ANDROID_KEYCODE_VOLUME_UP)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _volume_down(self) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_keycode(self.ANDROID_ACTION_DOWN, self.ANDROID_KEYCODE_VOLUME_DOWN)
            await self._client.control.send_keycode(self.ANDROID_ACTION_UP, self.ANDROID_KEYCODE_VOLUME_DOWN)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _back(self) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_keycode(self.ANDROID_ACTION_DOWN, self.ANDROID_KEYCODE_BACK)
            await self._client.control.send_keycode(self.ANDROID_ACTION_UP, self.ANDROID_KEYCODE_BACK)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _switch_app(self) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_keycode(self.ANDROID_ACTION_DOWN, self.ANDROID_KEYCODE_APP_SWITCH)
            await self._client.control.send_keycode(self.ANDROID_ACTION_UP, self.ANDROID_KEYCODE_APP_SWITCH)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}

    async def _home(self) -> dict[str, Any]:
        if self._client is None or self._client.control is None:
            return {"ok": False, "error": "control stream is not running"}
        try:
            await self._client.control.send_keycode(self.ANDROID_ACTION_DOWN, self.ANDROID_KEYCODE_HOME)
            await self._client.control.send_keycode(self.ANDROID_ACTION_UP, self.ANDROID_KEYCODE_HOME)
            return {"ok": True}
        except (BrokenPipeError, ConnectionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}


    # ------------------------------------------------------------------ #
    # Event pump
    # ------------------------------------------------------------------ #

    async def _pump_events(self, client: ScrcpyClient) -> None:
        try:
            async for event in client.av.events():
                self._put_event(self._serialize_event(event))
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def _serialize_event(self, event: AudioVideoEvent) -> dict[str, Any]:
        codec = event.codec.label if event.codec else None
        if event.kind is StreamKind.SESSION and event.session is not None:
            self._last_session = (event.session.width, event.session.height)
            return {
                "kind": "session",
                "codec": codec,
                "width": event.session.width,
                "height": event.session.height,
                "clientResized": event.session.client_resized,
            }
        return {
            "kind": event.kind.value,
            "codec": codec,
            "pts": event.pts,
            "config": event.config,
            "keyFrame": event.key_frame,
            "payload": base64.b64encode(event.payload).decode("ascii"),
        }

    # ------------------------------------------------------------------ #
    # Queue helpers
    # ------------------------------------------------------------------ #

    def _put_event(self, item: dict[str, Any]) -> None:
        try:
            self._events.put_nowait(item)
        except queue.Full:
            try:
                self._events.get_nowait()
            except queue.Empty:
                pass
            self._events.put_nowait(item)

    def _clear_queue(self) -> None:
        while True:
            try:
                self._events.get_nowait()
            except queue.Empty:
                return

    def _make_status(self) -> dict[str, Any]:
        if self._client is None:
            return {"running": False}
        return {
            "running": True,
            "deviceName": self._client.device_meta.device_name if self._client.device_meta else None,
        }

    def _submit(self, coro: Any) -> Any:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
