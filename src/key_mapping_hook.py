"""Key mapping global hook for auto-hide mouse feature."""

from __future__ import annotations

import threading
from autoxkit.hook import HookListener, KeyEvent


class KeyMappingHook:
    """Listens for LAlt key globally to control mouse auto-hide.

    When enabled, LAlt press -> notify frontend to show cursor
    LAlt release -> notify frontend to hide cursor
    """

    def __init__(self):
        self._enabled = False
        self._hook: HookListener | None = None
        self._thread: threading.Thread | None = None
        self._window = None
        self._alt_pressed = False

    def set_window(self, window):
        """Set the pywebview window reference for JS evaluation."""
        self._window = window

    def start(self):
        """Start the global hook listener."""
        if self._enabled:
            return
        self._enabled = True
        self._thread = threading.Thread(target=self._run_hook, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the global hook listener."""
        self._enabled = False
        if self._hook:
            try:
                self._hook.stop()
            except Exception:
                pass
            self._hook = None

    def _run_hook(self):
        """Run the hook listener in a separate thread."""
        def on_key(event: KeyEvent):
            if not self._enabled or not self._window:
                return
            # LAlt virtual key code = 0xA4
            if event.key_code != 0xA4:
                return
            try:
                if event.event_type == 0x0100:  # WM_KEYDOWN
                    if not self._alt_pressed:
                        self._alt_pressed = True
                        self._window.evaluate_js(
                            'window.dispatchEvent(new CustomEvent("km-show-cursor"))'
                        )
                elif event.event_type == 0x0101:  # WM_KEYUP
                    if self._alt_pressed:
                        self._alt_pressed = False
                        self._window.evaluate_js(
                            'window.dispatchEvent(new CustomEvent("km-hide-cursor"))'
                        )
            except Exception:
                pass

        try:
            self._hook = HookListener(on_key)
            self._hook.start()
            self._hook.wait()
        except Exception:
            pass
