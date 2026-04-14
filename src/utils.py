"""
utils.py
常用工具函数。
"""

import re
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


def generate_filename(url_or_path: str, has_summary: bool = True, is_local: bool = False) -> str:
    """根据 URL 或文件路径和是否有总结生成文件名"""
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if is_local:
        # 本地文件处理
        file_stem = Path(url_or_path).stem
        # 清理文件名中的特殊字符
        safe_stem = safe_filename(file_stem)
        platform = "local"
        video_id = safe_stem[:10]  # 取前 10 个字符作为 ID
    else:
        # 从 URL 中提取视频 ID
        if "bilibili.com" in url_or_path:
            # B 站视频 ID 格式：BV1xx411c7mu
            if "BV" in url_or_path:
                video_id = url_or_path.split("BV")[1].split("?")[0][:10]
                platform = "bilibili"
            else:
                video_id = "unknown"
                platform = "bilibili"
        elif "youtube.com" in url_or_path:
            # YouTube 视频 ID 格式：dQw4w9WgXcQ
            if "v=" in url_or_path:
                video_id = url_or_path.split("v=")[1].split("&")[0][:11]
                platform = "youtube"
            else:
                video_id = "unknown"
                platform = "youtube"
        elif "douyin.com" in url_or_path or "v.douyin.com" in url_or_path:
            # 抖音视频 ID 提取
            match = re.search(r'/video/(\d+)', url_or_path)
            if match:
                video_id = match.group(1)[:12]
                platform = "douyin"
            else:
                video_id = "unknown"
                platform = "douyin"
        else:
            video_id = "unknown"
            platform = "other"

    # 生成文件名
    if has_summary:
        filename = f"{platform}_{video_id}_{timestamp}_总结.md"
    else:
        filename = f"{platform}_{video_id}_{timestamp}_转录.txt"

    return filename

def get_platform(url: str) -> str:
    """
    判断视频链接平台类型。
    :param url: 视频链接
    :return: 'bilibili'/'youtube'/'tencent'/'iqiyi'/'youku'/'douyin'/'tiktok'/'other'
    """
    url = url.lower()
    if 'bilibili.com' in url:
        return 'bilibili'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'v.qq.com' in url or 'qq.com' in url:
        return 'tencent'
    elif 'iqiyi.com' in url:
        return 'iqiyi'
    elif 'youku.com' in url:
        return 'youku'
    elif 'douyin.com' in url or 'v.douyin.com' in url:
        return 'douyin'
    elif 'tiktok.com' in url or 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
        return 'tiktok'
    else:
        return 'other'

def safe_filename(name: str, ext: str = "") -> str:
    """
    生成安全的文件名，去除非法字符。
    :param name: 原始名称
    :param ext: 文件扩展名（如 .mp3）
    :return: 安全文件名
    """
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    name = name.strip().replace(' ', '_')
    if ext and not name.endswith(ext):
        name += ext
    return name

class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_color(msg: str, color: str = Color.OKGREEN):
    print(f"{color}{msg}{Color.ENDC}") 