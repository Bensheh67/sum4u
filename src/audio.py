"""
audio.py
负责下载视频音频并进行音频提取。
"""

import asyncio
import os
from pathlib import Path
try:
    from moviepy.audio.io.AudioFileClip import AudioFileClip
except ImportError:
    raise ImportError("未找到 moviepy，请先运行 pip install moviepy 安装依赖。")
import subprocess
from .utils import get_platform

# 仅在需要时导入 bilix

async def download_bilibili_audio(url: str, output_dir: str = "downloads") -> str:
    """使用 yt-dlp 下载 Bilibili 视频音频"""
    os.makedirs(output_dir, exist_ok=True)
    audio_path = Path(output_dir) / "bilibili_output.mp3"

    try:
        # 使用 yt-dlp 下载 Bilibili 视频并提取音频
        # 修复URL中的转义字符
        import urllib.parse
        decoded_url = urllib.parse.unquote(url)

        # 额外处理：去除可能的双反斜杠转义
        import re
        decoded_url = re.sub(r'\\\\', r'\\', decoded_url)  # 将双反斜杠替换为单反斜杠
        decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

        cmd = [
            "yt-dlp",
            "-x",  # 提取音频
            "--audio-format", "mp3",  # 转换为 mp3
            "--audio-quality", "0",  # 最高音质
            "--force-overwrites",  # 强制覆盖已存在的文件
            "-o", str(audio_path),  # 输出文件
            "--cookies-from-browser", "chrome",  # 使用浏览器cookies（如果需要）
            decoded_url
        ]

        print(f"正在下载Bilibili视频: {decoded_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Bilibili下载完成")

        # 检查文件是否存在
        if not audio_path.exists():
            # 如果指定名称不存在，查找下载的文件
            downloaded_files = list(Path(output_dir).glob("*.mp3"))
            if downloaded_files:
                audio_path = downloaded_files[0]
            else:
                raise RuntimeError("未找到下载的音频文件")

        return str(audio_path)

    except subprocess.CalledProcessError as e:
        print(f"yt-dlp 下载失败: {e}")
        print(f"错误输出: {e.stderr}")
        # 尝试不使用cookies的方式下载
        try:
            print("尝试不使用浏览器cookies下载...")
            # 再次确保URL已解码
            import urllib.parse
            decoded_url = urllib.parse.unquote(url)
            import re
            decoded_url = re.sub(r'\\\\', r'\\', decoded_url)  # 将双反斜杠替换为单反斜杠
            decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

            cmd = [
                "yt-dlp",
                "-x",  # 提取音频
                "--audio-format", "mp3",  # 转换为 mp3
                "--audio-quality", "0",  # 最高音质
                "--force-overwrites",  # 强制覆盖已存在的文件
                "-o", str(audio_path),  # 输出文件
                decoded_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("Bilibili下载完成（无cookies）")

            # 检查文件是否存在
            if not audio_path.exists():
                downloaded_files = list(Path(output_dir).glob("*.mp3"))
                if downloaded_files:
                    audio_path = downloaded_files[0]
                else:
                    raise RuntimeError("未找到下载的音频文件")

            return str(audio_path)
        except subprocess.CalledProcessError as e2:
            print(f"yt-dlp 下载失败（无cookies）: {e2}")
            print(f"错误输出: {e2.stderr}")
            raise RuntimeError(f"Bilibili视频下载失败: {e2}")
    except Exception as e:
        print(f"Bilibili下载出错: {e}")
        raise RuntimeError(f"Bilibili视频下载失败: {e}")

async def download_youtube_audio(url: str, output_dir: str = "downloads") -> str:
    os.makedirs(output_dir, exist_ok=True)
    audio_path = Path(output_dir) / "youtube_output.mp3"

    # 修复URL中的转义字符
    import urllib.parse
    decoded_url = urllib.parse.unquote(url)

    # 额外处理：去除可能的双反斜杠转义
    import re
    decoded_url = re.sub(r'\\\\', r'\\', decoded_url)  # 将双反斜杠替换为单反斜杠
    decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--force-overwrites",  # 强制覆盖已存在的文件
        "--no-playlist",  # 只下载单个视频，不下载播放列表
        "-o", str(audio_path),
        decoded_url
    ]
    subprocess.run(cmd, check=True)
    return str(audio_path)

async def download_audio_from_url(url: str, output_dir: str = "downloads") -> str:
    platform = get_platform(url)
    if platform == 'bilibili':
        return await download_bilibili_audio(url, output_dir)
    elif platform == 'youtube':
        return await download_youtube_audio(url, output_dir)
    else:
        raise ValueError(f"暂不支持该平台: {url}")

def download_audio(url: str, output_dir: str = "downloads") -> str:
    return asyncio.run(download_audio_from_url(url, output_dir)) 