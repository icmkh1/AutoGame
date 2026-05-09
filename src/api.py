
import json
from pathlib import Path

class Api:
    def __init__(self, logger, macro_file, macro):
        self.logger = logger
        self.macro_file = macro_file
        self.macro = macro
        self._no_key_names = ['MLeft', 'MRight', 'Middle', 'side1', 'side2']

        self._window = None
        self._maximized = False
        self._config_path = Path(__file__).parent.parent / 'data' / 'config' / 'config.json'
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        config_dir = self._config_path.parent
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f'加载配置文件 报错信息：{e}')
        return {}

    def _save_config(self, config):
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.logger.error(f'保存配置文件 报错信息：{e}')
            return False

    def get_macro_files(self):
        return self.macro_file.get_macro_files()

    def load_macrofile(self, file_name: str):
        return self.macro_file.load_macro_file(file_name)

    def save_macrofile(self, file_name: str, macro_file: str):
        return self.macro_file.save_macro_file(file_name, macro_file)

    def create_new_file(self):
        return self.macro_file.create_new_file()

    def rename_file(self, old_name: str, new_name: str):
        return self.macro_file.rename_file(old_name, new_name)

    def open_folder(self, file_name: str):
        return self.macro_file.open_folder(file_name)

    def delete_file(self, file_name: str):
        return self.macro_file.delete_file(file_name)

    def get_key_name(self):
        key_name = self.macro.get_key_name()
        if key_name in self._no_key_names:
            return False
        return key_name

    def set_main_switch_key(self, key: str):
        self.macro.set_main_switch_key(key)

    def set_window(self, window):
        self._window = window

    def get_app_info(self):
        return {
            'name': 'AutoGame',
            'version': '0.3.0'
        }

    def minimize(self):
        if self._window:
            self._window.minimize()

    def close(self):
        if self._window:
            config = self._load_config()
            minimize_to_tray = config.get('minimizeToTray', True)
            if minimize_to_tray:
                self._window.hide()
            else:
                self._window.destroy()

    def toggle_maximize(self):
        if self._window:
            if self._maximized:
                self._window.restore()
                self._maximized = False
                return False
            else:
                self._window.maximize()
                self._maximized = True
                return True
        return False

    def get_config(self):
        config = self._load_config()
        self.set_main_switch_key(config['macroSwitch'])
        return config

    def save_config(self, config):
        self.set_main_switch_key(config['macroSwitch'])
        return self._save_config(config)

    def __dir__(self):
        return [
            'get_app_info', 'minimize', 'close', 'toggle_maximize',
            'get_config', 'save_config',
            'get_macro_files', 'load_macrofile', 'save_macrofile',
            'create_new_file', 'rename_file', 'open_folder', 'delete_file',
            'get_key_name', 'set_main_switch_key'
        ]
