#!/usr/bin/env python3
"""
setup_api_keys.py
API密钥配置脚本 - 帮助用户设置API密钥
"""

import os
import sys
import getpass
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.config import config_manager


def setup_api_keys():
    """交互式设置API密钥"""
    print("🎤 音频/视频总结工具 - API密钥配置向导")
    print("=" * 50)
    print("此向导将帮助您配置AI服务的API密钥")
    print("配置信息将保存在 config.json 文件中")
    print()

    # 显示当前配置
    print("当前配置:")
    for provider, key in config_manager.config["api_keys"].items():
        status = "已设置" if key else "未设置"
        print(f"  {provider.capitalize()} API密钥: {status}")
    print(f"  默认模型: {config_manager.get_default_model()}")
    print()

    while True:
        print("请选择操作:")
        print("1. 设置API密钥")
        print("2. 查看当前配置")
        print("3. 退出")

        choice = input("\n请输入选项 (1-3): ").strip()

        if choice == "1":
            configure_keys()
        elif choice == "2":
            show_current_config()
        elif choice == "3":
            print("再见！")
            break
        else:
            print("无效选项，请重新输入")


def configure_keys():
    """配置API密钥"""
    print("\n设置API密钥 (直接回车跳过):")

    providers = ["deepseek", "openai", "anthropic"]

    for provider in providers:
        current_key = config_manager.get_api_key(provider)
        prompt_text = f"{provider.upper()} API密钥"

        if current_key:
            prompt_text += f" (当前已配置，回车保持不变)"

        # 使用getpass隐藏输入
        new_key = getpass.getpass(f"请输入{prompt_text}: ")

        if new_key:  # 如果输入了新密钥，则更新
            config_manager.set_api_key(provider, new_key)
            print(f"✓ {provider.upper()} API密钥已更新")
        elif current_key and not new_key:
            print(f"- 保持当前 {provider.upper()} API密钥不变")
        else:
            print(f"- {provider.upper()} API密钥未设置")

    # 设置默认模型
    print(f"\n当前默认模型: {config_manager.get_default_model()}")
    new_model = input("输入新的默认模型 (回车跳过): ").strip()
    if new_model:
        config_manager.set_default_model(new_model)
        print(f"✓ 默认模型已更新为: {new_model}")

    print("\n✅ API密钥配置完成！")


def show_current_config():
    """显示当前配置"""
    print("\n当前配置详情:")
    print("-" * 30)
    print("API密钥状态:")
    for provider, key in config_manager.config["api_keys"].items():
        status = "已设置" if key else "未设置"
        masked_key = f"{key[:5]}..." if key else ""
        print(f"  {provider.capitalize()}: {status} {masked_key}")

    print(f"\n默认模型: {config_manager.get_default_model()}")
    print(f"配置文件位置: {config_manager.config_file.absolute()}")
    print()


if __name__ == "__main__":
    setup_api_keys()