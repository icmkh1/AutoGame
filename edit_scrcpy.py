import json
with open("temp_scrcpy.txt", "r", encoding="utf-8") as f:
    content = f.read()
android_map = {
    "A": 29, "B": 30, "C": 31, "D": 32, "E": 33, "F": 34, "G": 35, "H": 36,
    "I": 37, "J": 38, "K": 39, "L": 40, "M": 41, "N": 42, "O": 43, "P": 44,
    "Q": 45, "R": 46, "S": 47, "T": 48, "U": 49, "V": 50, "W": 51, "X": 52,
    "Y": 53, "Z": 54,
    "0": 7, "1": 8, "2": 9, "3": 10, "4": 11, "5": 12, "6": 13, "7": 14, "8": 15, "9": 16,
    "Space": 62, "Enter": 66, "Back": 4, "Tab": 61, "Esc": 111,
    "CapsLock": 115,
    "LShift": 59, "RShift": 60, "LCtrl": 113, "RCtrl": 114, "LAlt": 57, "RAlt": 58,
    "LWin": 551, "RWin": 552,
    "Menu": 82,
    "Left": 21, "Up": 19, "Right": 22, "Down": 20,
    "Insert": 214, "Delete": 67, "Home": 3, "End": 123, "PgUp": 92, "PgDown": 93,
    "Numpad0": 144, "Numpad1": 145, "Numpad2": 146, "Numpad3": 147,
    "Numpad4": 148, "Numpad5": 149, "Numpad6": 150, "Numpad7": 151,
    "Numpad8": 152, "Numpad9": 153,
    "Multiply": 78, "Add": 81, "Subtract": 69, "Divide": 88,
    "Numlock": 143, "Decimal": 158,
    "F1": 131, "F2": 132, "F3": 133, "F4": 134, "F5": 135, "F6": 136,
    "F7": 137, "F8": 138, "F9": 139, "F10": 140, "F11": 141, "F12": 142,
}
amap = json.dumps(android_map, indent=4)
insert = f"""

    # Android keycode map (key name -> Android keycode)
    ANDROID_KEYCODE_MAP = {amap}

    # Mouse button names that map to touch events
    MOUSE_BUTTON_MAP_ADB = {{
        'MLeft': 'touch',
        'MRight': 'touch',
        'Middle': 'touch',
        'MSide1': 'touch',
        'MSide2': 'touch',
    }}

    def __init__(self) -> None:
        super().__init__()
        self._active_key_mapping = None
        self._key_listener_running = False
"""
idx = content.find("    def __init__(self) -> None:")
if idx >= 0:
    content = content[:idx] + insert + content[idx:]
with open("temp_scrcpy.txt", "w", encoding="utf-8") as f:
    f.write(content)
print(f"OK: {len(content)}")
