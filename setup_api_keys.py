#!/usr/bin/env python3
"""
API密钥配置向导
"""

import json
import os
from pathlib import Path

def setup_api_keys():
    """设置API密钥的交互式向导"""
    print("=" * 60)
    print("API密钥配置向导")
    print("=" * 60)
    
    print("\n欢迎使用音频/视频总结工具！")
    print("在开始使用前，请配置您的API密钥。")
    
    # 检查配置文件是否存在
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "api_keys": {
                "deepseek": "",
                "openai": "",
                "anthropic": "",
                "tikhub": ""
            },
            "default_model": "deepseek-chat",
            "default_language": "auto",
            "external_apis": {
                "douyin_api_endpoint": "https://api.tikhub.io"
            },
            "output_settings": {
                "transcription_folder": "transcriptions",
                "summary_folder": "summaries",
                "download_folder": "downloads"
            }
        }
    
    print("\n当前配置状态:")
    api_keys = config.get("api_keys", {})
    
    providers = {
        "deepseek": "DeepSeek API密钥",
        "openai": "OpenAI API密钥", 
        "anthropic": "Anthropic API密钥",
        "tikhub": "TikHub API密钥 (用于抖音/TikTok)"
    }
    
    for provider, desc in providers.items():
        status = "已配置" if api_keys.get(provider) else "未配置"
        print(f"  • {desc}: {status}")
    
    print("\n" + "-" * 60)
    print("API密钥配置说明:")
    print("1. DeepSeek API密钥: 用于AI摘要生成")
    print("2. TikHub API密钥: 用于处理抖音/TikTok视频")
    print("   - 访问 https://user.tikhub.io/users/signin 注册账户")
    print("   - 登录后进入用户中心 > API密钥 > 创建API密钥")
    print("   - 复制API密钥并在此处输入")
    print("-" * 60)
    
    # 配置API密钥
    for provider, desc in providers.items():
        current_key = api_keys.get(provider, "")
        if current_key:
            print(f"\n{desc}:")
            print(f"  当前已配置: {current_key[:10]}...{current_key[-5:]}")
            update = input("  是否更新? (y/N): ").lower().strip()
            if update != 'y':
                continue
        
        print(f"\n请输入{desc}:")
        if provider == "tikhub":
            print("  (可访问 https://user.tikhub.io/users/signin 获取免费API密钥)")
        
        new_key = input(f"  {desc}: ").strip()
        if new_key:
            api_keys[provider] = new_key
            print(f"  ✓ {desc}已更新")
        else:
            print(f"  - 未更新{desc}")
    
    # 更新配置
    config["api_keys"] = api_keys
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("配置完成！")
    print("=" * 60)
    
    print("\n配置摘要:")
    for provider, desc in providers.items():
        status = "已配置" if config["api_keys"].get(provider) else "未配置"
        print(f"  • {desc}: {status}")
    
    print("\n现在您可以启动WebUI开始使用工具了！")
    print("运行命令: ./webui.sh 或 python3 -m src.webui")
    
    return config

if __name__ == "__main__":
    setup_api_keys()