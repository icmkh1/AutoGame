import os
import sys
import urllib.request
import tempfile
import subprocess
import ctypes
import winreg


class WebView2Checker:
    def __init__(self, logger=None):
        self.logger = logger

    def check_runtime(self):
        if self.check_via_registry():
            return True
        if self.check_via_dll():
            return True
        if self.check_via_folder():
            return True
        return False

    def check_via_registry(self):
        try:
            reg_path = r'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
                value, _ = winreg.QueryValueEx(key, 'pv')
                if value:
                    self.logger.info(f'通过注册表检测到WebView2运行时版本: {value}')
                    return True
        except FileNotFoundError:
            pass
        except Exception as e:
            self.logger.debug(f'注册表检测失败: {e}')

        try:
            reg_path = r'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, 'pv')
                if value:
                    self.logger.info(f'通过注册表检测到WebView2运行时版本: {value}')
                    return True
        except FileNotFoundError:
            pass
        except Exception as e:
            self.logger.debug(f'注册表检测失败: {e}')

        try:
            reg_path = r'SOFTWARE\Microsoft\WebView2\InstalledVersions'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            path, _ = winreg.QueryValueEx(subkey, 'Path')
                            if path and os.path.exists(path):
                                self.logger.info(f'通过注册表检测到WebView2运行时: {path}')
                                return True
                        i += 1
                    except OSError:
                        break
        except FileNotFoundError:
            pass
        except Exception as e:
            self.logger.debug(f'注册表检测失败: {e}')

        return False

    def check_via_dll(self):
        try:
            ctypes.WinDLL('WebView2Loader.dll')
            self.logger.info('通过DLL加载检测到WebView2运行时')
            return True
        except WindowsError:
            pass

        try:
            ctypes.WinDLL('CoreWebView2.dll')
            self.logger.info('通过DLL加载检测到WebView2运行时')
            return True
        except WindowsError:
            pass

        try:
            system32_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
            webview2_dll = os.path.join(system32_path, 'CoreWebView2.dll')
            if os.path.exists(webview2_dll):
                ctypes.WinDLL(webview2_dll)
                self.logger.info(f'通过DLL加载检测到WebView2运行时: {webview2_dll}')
                return True
        except Exception as e:
            self.logger.debug(f'DLL检测失败: {e}')

        return False

    def check_via_folder(self):
        common_paths = [
            r'C:\Program Files (x86)\Microsoft\EdgeWebView\Application',
            r'C:\Program Files\Microsoft\EdgeWebView\Application',
            r'C:\Program Files (x86)\Microsoft\EdgeCore\WebView2',
            r'C:\Program Files\Microsoft\EdgeCore\WebView2'
        ]

        for base_path in common_paths:
            if os.path.exists(base_path):
                versions = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and d.replace('.', '').isdigit()]
                if versions:
                    versions.sort(reverse=True)
                    latest_version = versions[0]
                    dll_path = os.path.join(base_path, latest_version, 'CoreWebView2.dll')
                    if os.path.exists(dll_path):
                        self.logger.info(f'通过目录检测到WebView2运行时: {dll_path}')
                        return True
        return False

    def download_installer(self):
        url = 'https://go.microsoft.com/fwlink/p/?LinkId=2124703'
        try:
            with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
                installer_path = temp_file.name

            self.logger.info(f'开始下载WebView2安装程序到: {installer_path}')
            urllib.request.urlretrieve(url, installer_path)
            self.logger.info('WebView2安装程序下载完成')
            return installer_path
        except Exception as e:
            self.logger.error(f'下载WebView2安装程序失败: {e}')
            return None

    def install(self, installer_path):
        try:
            self.logger.info('开始安装WebView2...')
            result = subprocess.run(
                [installer_path, '/silent', '/install'],
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info(f'WebView2安装成功: {result.stdout}')
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f'WebView2安装失败: {e.stderr}')
            return False

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            self.logger.debug(f'检查管理员权限失败: {e}')
            return False

    def run_as_admin(self):
        if not self.is_admin():
            self.logger.info('需要管理员权限，尝试提升权限...')
            ctypes.windll.shell32.ShellExecuteW(
                None,
                'runas',
                sys.executable,
                ' '.join(sys.argv),
                None,
                1
            )
            sys.exit(0)

    def check_and_prompt(self):
        if self.check_runtime():
            return

        self.logger.warning('未检测到WebView2运行时环境')

        if not self.is_admin():
            self.run_as_admin()

        installer_path = self.download_installer()
        if not installer_path:
            self.logger.error('无法下载WebView2安装程序，请手动安装')
            return

        if self.install(installer_path):
            self.logger.info('WebView2安装完成')
        else:
            self.logger.error('WebView2安装失败，请手动安装')

        if os.path.exists(installer_path):
            os.remove(installer_path)
