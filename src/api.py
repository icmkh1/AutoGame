

class Api:
    def __init__(self, logger, file_manager, macro):
        self.logger = logger
        self.file_manager = file_manager
        self.macro = macro
        self._no_key_names = ['MLeft', 'MRight', 'Middle', 'side1', 'side2']

        self._window = None
        self._maximized = False

    def get_config_file(self):
        config = self.file_manager.load_config_file()
        self.macro.set_main_switch_key(config['macroSwitch'])
        return config

    def save_config_file(self, config):
        self.macro.set_main_switch_key(config['macroSwitch'])
        return self.file_manager.save_config_file(config)

    def get_macro_files(self):
        return self.file_manager.get_macro_files()

    def load_macrofile(self, file_name: str):
        return self.file_manager.load_macro_file(file_name)

    def save_macrofile(self, file_name: str, macro_file: str):
        return self.file_manager.save_macro_file(file_name, macro_file)

    def create_new_file(self):
        return self.file_manager.create_new_file()

    def rename_file(self, old_name: str, new_name: str):
        return self.file_manager.rename_file(old_name, new_name)

    def open_folder(self, file_name: str):
        return self.file_manager.open_folder(file_name)

    def delete_file(self, file_name: str):
        return self.file_manager.delete_file(file_name)

    def get_key_name(self):
        key_name = self.macro.get_key_name()
        if key_name in self._no_key_names:
            return False
        return key_name

    def set_window(self, window):
        self._window = window

    def get_app_info(self):
        return {
            'name': 'AutoGame',
            'version': '0.5.0'
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

    def __dir__(self):
        return [
            'get_app_info', 'minimize', 'close', 'toggle_maximize',
            'get_config_file', 'save_config_file', 'get_key_name',
            'get_macro_files', 'load_macrofile', 'save_macrofile',
            'create_new_file', 'rename_file', 'open_folder', 'delete_file',
        ]
