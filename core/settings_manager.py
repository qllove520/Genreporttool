import json
import os
import traceback


class SettingsManager:
    def __init__(self, app_prefix="default"):
        self.app_prefix = app_prefix

        script_dir = os.path.dirname(os.path.abspath(__file__))  # core 文件夹的路径
        project_root = os.path.join(script_dir, '..')  # 上一级目录，即项目根目录
        self.config_dir = os.path.join(os.getcwd())

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def save_settings(self, settings_type: str, settings_data: dict, log_callback=None):
        """Saves the settings to a JSON file with UTF-8 encoding."""
        file_path = os.path.join(self.config_dir, f"{settings_type}.txt")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=4)
            if log_callback:
                log_callback(f"设置已保存到: {os.path.basename(file_path)}", False)
        except Exception as e:
            if log_callback:
                log_callback(f"保存设置失败: {e}\n{traceback.format_exc()}", True)

    def load_settings(self, settings_type: str, default_settings: dict, log_callback=None) -> dict:
        """Loads settings from a JSON file, attempting UTF-8 first, then GBK."""
        file_path = os.path.join(self.config_dir, f"{settings_type}.txt")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                if log_callback:
                    log_callback(f"已加载设置文件: {os.path.basename(file_path)}", False)
                return settings
            except UnicodeDecodeError:
                if log_callback:
                    log_callback(f"警告: 设置文件 '{os.path.basename(file_path)}' 非 UTF-8 编码，尝试 GBK...", False)
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        settings = json.load(f)
                    if log_callback:
                        log_callback(f"已成功加载 GBK 编码的设置文件: {os.path.basename(file_path)}", False)
                    try:
                        self.save_settings(settings_type, settings, log_callback)
                        if log_callback:
                            log_callback(f"已将 '{os.path.basename(file_path)}' 重新保存为 UTF-8。", False)
                    except Exception as resave_e:
                        if log_callback:
                            log_callback(f"重新保存为 UTF-8 失败: {resave_e}\n{traceback.format_exc()}", True)
                    return settings
                except Exception as e:
                    if log_callback:
                        log_callback(f"加载设置文件失败 (尝试 GBK): {e}\n{traceback.format_exc()}", True)
                        log_callback(f"将使用默认设置。", False)
                    return default_settings
            except Exception as e:
                if log_callback:
                    log_callback(f"加载设置文件失败: {e}\n{traceback.format_exc()}", True)
                    log_callback(f"将使用默认设置。", False)
                return default_settings
        else:
            if log_callback:
                log_callback(f"未找到 {os.path.basename(file_path)} 的设置文件，将使用默认值。", False)
            return default_settings