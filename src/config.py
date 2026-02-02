"""
config.py
配置管理模块 - 处理API密钥和其他配置项
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.default_config = {
            "api_keys": {
                "deepseek": "",
                "openai": "",
                "anthropic": ""
            },
            "default_model": "deepseek-chat",
            "default_language": "auto",
            "output_settings": {
                "transcription_folder": "transcriptions",
                "summary_folder": "summaries",
                "download_folder": "downloads"
            }
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在则创建默认配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置，确保新字段存在
                    merged_config = self._merge_configs(self.default_config, loaded_config)
                    return merged_config
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")

        # 返回默认配置
        return self.default_config.copy()

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """合并默认配置和已加载的配置"""
        result = default.copy()

        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False

    def set_api_key(self, provider: str, api_key: str):
        """设置API密钥"""
        if provider in self.config["api_keys"]:
            self.config["api_keys"][provider] = api_key
            self.save_config()

    def get_api_key(self, provider: str) -> Optional[str]:
        """获取API密钥"""
        return self.config["api_keys"].get(provider)

    def set_default_model(self, model: str):
        """设置默认模型"""
        self.config["default_model"] = model
        self.save_config()

    def get_default_model(self) -> str:
        """获取默认模型"""
        return self.config["default_model"]


# 全局配置实例
config_manager = ConfigManager()


def get_api_key(provider: str) -> Optional[str]:
    """获取API密钥的便捷函数"""
    return config_manager.get_api_key(provider)


def set_api_key(provider: str, api_key: str):
    """设置API密钥的便捷函数"""
    config_manager.set_api_key(provider, api_key)


def initialize_config():
    """初始化配置（如果不存在的话）"""
    if not config_manager.config_file.exists():
        config_manager.save_config()
        print("配置文件已创建，请在 config.json 中设置您的 API 密钥")


# 首次导入时初始化配置
initialize_config()