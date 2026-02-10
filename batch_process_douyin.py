#!/usr/bin/env python3
"""
批量处理抖音视频示例脚本
"""

import os
import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def batch_process_douyin_videos():
    """批量处理抖音视频的示例"""
    print("=" * 60)
    print("批量处理抖音视频示例")
    print("=" * 60)
    
    # 从环境变量获取API密钥
    api_key = os.getenv('TIKHUB_API_KEY')
    if not api_key:
        print("⚠️  警告: 未设置环境变量 TIKHUB_API_KEY")
        print("   请先设置环境变量，或在WebUI中配置API密钥")
        print("   设置方法: export TIKHUB_API_KEY='your_api_key_here'")
        print()
        
        # 尝试从配置获取API密钥
        from src.config import config_manager
        api_key = config_manager.config.get("api_keys", {}).get("tikhub")
        if not api_key:
            print("❌ 错误: 未配置TikHub API密钥")
            print("   请先配置API密钥后再运行此脚本")
            return False
        else:
            print("✓ 使用配置文件中的API密钥")
    else:
        print("✓ 使用环境变量中的API密钥")
    
    # 示例抖音分享链接列表
    douyin_urls = [
        "6.39 03/26 14:06 [抖音] https://v.douyin.com/iJN1234/ 复制此链接，打开抖音，直接观看视频！",
        "【抖音】[链接]https://v.douyin.com/abc123/  ",
        "Check out this TikTok: https://vm.tiktok.com/TTSomeID/",
        "https://www.tiktok.com/@username/video/1234567890123456789",
        # 添加更多示例链接...
    ]
    
    print(f"\n准备处理 {len(douyin_urls)} 个视频链接...")
    
    # 显示要处理的链接
    for i, url in enumerate(douyin_urls, 1):
        print(f"  {i}. {url[:60]}{'...' if len(url) > 60 else ''}")
    
    print("\n开始批量处理...")
    
    try:
        from src.douyin_handler import batch_process_douyin_urls
        
        # 执行批量处理
        results = batch_process_douyin_urls(douyin_urls, "downloads", api_key)
        
        print(f"\n批量处理完成！共处理 {len(results)} 个链接")
        
        # 统计结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        
        print(f"成功: {success_count}, 失败: {error_count}")
        
        # 显示详细结果
        print("\n详细结果:")
        for i, result in enumerate(results, 1):
            status_icon = "✓" if result['status'] == 'success' else "✗"
            print(f"  {status_icon} {i}. {result['url'][:50]}...")
            if result['status'] == 'success':
                print(f"      音频路径: {result['audio_path']}")
            else:
                print(f"      错误: {result.get('error', 'Unknown error')}")
        
        # 保存结果到文件
        output_file = Path("batch_processing_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_environment_variables():
    """设置环境变量的说明"""
    print("\n" + "=" * 60)
    print("环境变量设置说明")
    print("=" * 60)
    
    print("""
    为了安全地使用API密钥，建议使用环境变量：
    
    1. 临时设置（当前终端会话有效）:
       export TIKHUB_API_KEY="your_actual_api_key_here"
       
    2. 永久设置（添加到shell配置文件）:
       echo 'export TIKHUB_API_KEY="your_actual_api_key_here"' >> ~/.zshrc
       source ~/.zshrc
       
    3. 或者创建 .env 文件:
       echo 'TIKHUB_API_KEY=your_actual_api_key_here' > .env
    """)

if __name__ == "__main__":
    success = batch_process_douyin_videos()
    
    if not success:
        setup_environment_variables()
    
    print("\n💡 提示: 在生产环境中，强烈建议使用环境变量存储API密钥")
    print("    而不是在代码或配置文件中硬编码API密钥。")