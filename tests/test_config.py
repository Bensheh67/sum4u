"""
测试配置模块
"""

import pytest
import json
import tempfile
import os
from pathlib import Path


class TestConfigManager:
    """测试 ConfigManager 类"""

    def test_default_config_has_all_providers(self):
        """测试默认配置包含所有 API 提供商"""
        from src.config import ConfigManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_config = f.name

        try:
            manager = ConfigManager(config_file=temp_config)
            assert "deepseek" in manager.config["api_keys"]
            assert "openai" in manager.config["api_keys"]
            assert "anthropic" in manager.config["api_keys"]
            assert "tikhub" in manager.config["api_keys"]
        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)

    def test_set_and_get_api_key(self):
        """测试设置和获取 API 密钥"""
        from src.config import ConfigManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_config = f.name

        try:
            manager = ConfigManager(config_file=temp_config)
            manager.set_api_key("deepseek", "test-key-123")
            assert manager.get_api_key("deepseek") == "test-key-123"
        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)

    def test_get_api_key_returns_none_for_unknown_provider(self):
        """测试获取未知提供商的密钥返回 None"""
        from src.config import ConfigManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_config = f.name

        try:
            manager = ConfigManager(config_file=temp_config)
            assert manager.get_api_key("unknown_provider") is None
        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)


class TestGetApiKeyFromEnv:
    """测试从环境变量获取 API 密钥"""

    def test_get_api_key_prefers_env_variable(self):
        """测试优先从环境变量获取"""
        from src.config import get_api_key
        import os

        os.environ["DEEPSEEK_API_KEY"] = "env-deepseek-key"
        try:
            key = get_api_key("deepseek")
            assert key == "env-deepseek-key"
        finally:
            del os.environ["DEEPSEEK_API_KEY"]

    def test_get_api_key_falls_back_to_config(self):
        """测试环境变量未设置时回退到配置文件"""
        from src.config import get_api_key, ConfigManager
        import os

        # 确保环境变量未设置
        for key in ["DEEPSEEK_API_KEY", "TIKHUB_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            if key in os.environ:
                del os.environ[key]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_config = f.name

        try:
            # 写入配置
            config_data = {"api_keys": {"deepseek": "config-deepseek-key"}}
            with open(temp_config, "w") as f:
                json.dump(config_data, f)

            # 重新创建 manager（需要 monkeypatch）
            import src.config
            original_manager = src.config.config_manager
            src.config.config_manager = ConfigManager(config_file=temp_config)

            key = get_api_key("deepseek")
            assert key == "config-deepseek-key"

            src.config.config_manager = original_manager
        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)