"""
utils.py
常用工具函数。
"""

import re
import os
from urllib.parse import urlparse

def get_platform(url: str) -> str:
    """
    判断视频链接平台类型。
    :param url: 视频链接
    :return: 'bilibili'/'youtube'/'tencent'/'iqiyi'/'youku'/'other'
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