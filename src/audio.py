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
from .douyin_handler import is_douyin_url, process_douyin_url

# 仅在需要时导入 bilix

async def download_bilibili_audio(url: str, output_dir: str = "downloads") -> str:
    """使用 yt-dlp 下载 Bilibili 视频音频"""
    os.makedirs(output_dir, exist_ok=True)

    # 从 URL 中提取视频 ID 用于生成唯一文件名
    video_id = "unknown"
    if "BV" in url:
        video_id = url.split("BV")[1].split("?")[0][:12]
    elif "/video/" in url:
        video_id = url.split("/video/")[-1].split("?")[0][:12]

    audio_path = Path(output_dir) / f"bilibili_{video_id}.mp3"

    try:
        # 使用 yt-dlp 下载 Bilibili 视频并提取音频
        # 修复 URL 中的转义字符
        import urllib.parse
        decoded_url = urllib.parse.unquote(url)

        # 额外处理：去除可能的双反斜杠转义
        import re
        decoded_url = re.sub(r'\\\\', r'\\', decoded_url)  # 将双反斜杠替换为单反斜杠
        decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

        # 下载前删除已存在的旧文件，确保不会复用旧内容
        if audio_path.exists():
            print(f"删除旧的音频文件：{audio_path}")
            audio_path.unlink()

        cmd = [
            "yt-dlp",
            "-x",  # 提取音频
            "--audio-format", "mp3",  # 转换为 mp3
            "--audio-quality", "0",  # 最高音质
            "--force-overwrites",  # 强制覆盖已存在的文件
            "--no-update",  # 不检查更新
            "--extractor-retries", "5",  # 提取器重试次数
            "-o", str(audio_path),  # 输出文件
            decoded_url
        ]

        print(f"正在下载 Bilibili 视频：{decoded_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Bilibili 下载完成")

        # 验证下载结果
        if audio_path.exists():
            file_size = audio_path.stat().st_size
            print(f"音频文件大小：{file_size / 1024 / 1024:.1f} MB")
        else:
            # 如果指定名称不存在，查找下载的文件
            downloaded_files = list(Path(output_dir).glob("*.mp3"))
            if downloaded_files:
                audio_path = downloaded_files[0]
                print(f"找到下载文件：{audio_path}")
            else:
                raise RuntimeError("未找到下载的音频文件")

        return str(audio_path)

    except subprocess.CalledProcessError as e:
        print(f"yt-dlp 下载失败：{e}")
        print(f"错误输出：{e.stderr}")
        # 下载失败时清理可能产生的部分文件
        if audio_path.exists():
            print(f"清理下载失败的文件：{audio_path}")
            audio_path.unlink()
        # 尝试不使用 cookies 的方式下载
        try:
            print("尝试不使用浏览器 cookies 下载...")
            # 再次确保 URL 已解码
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
                "--no-update",  # 不检查更新
                "--extractor-retries", "5",  # 提取器重试次数
                "-o", str(audio_path),  # 输出文件
                decoded_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("Bilibili 下载完成（无 cookies）")

            # 检查文件是否存在
            if audio_path.exists():
                file_size = audio_path.stat().st_size
                print(f"音频文件大小：{file_size / 1024 / 1024:.1f} MB")
                return str(audio_path)
            else:
                downloaded_files = list(Path(output_dir).glob("*.mp3"))
                if downloaded_files:
                    audio_path = downloaded_files[0]
                    print(f"找到下载文件：{audio_path}")
                    return str(audio_path)
                else:
                    raise RuntimeError("未找到下载的音频文件")
        except subprocess.CalledProcessError as e2:
            print(f"yt-dlp 下载失败（无 cookies）: {e2}")
            print(f"错误输出：{e2.stderr}")
            # 下载失败时清理可能产生的部分文件
            if audio_path.exists():
                print(f"清理下载失败的文件：{audio_path}")
                audio_path.unlink()
            raise RuntimeError(f"Bilibili 视频下载失败：{e2}")
    except Exception as e:
        print(f"Bilibili 下载出错：{e}")
        # 其他异常时也清理文件
        if audio_path.exists():
            print(f"清理异常文件：{audio_path}")
            audio_path.unlink()
        raise RuntimeError(f"Bilibili 视频下载失败：{e}")

async def download_youtube_audio(url: str, output_dir: str = "downloads") -> str:
    os.makedirs(output_dir, exist_ok=True)

    # 修复 URL 中的转义字符
    import urllib.parse
    decoded_url = urllib.parse.unquote(url)

    # 额外处理：去除可能的双反斜杠转义
    import re
    decoded_url = re.sub(r'\\\\', r'\\', decoded_url)  # 将双反斜杠替换为单反斜杠
    decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

    # 从 URL 中提取视频 ID 用于生成唯一文件名
    video_id = "unknown"
    if "v=" in decoded_url:
        video_id = decoded_url.split("v=")[1].split("&")[0][:11]
    elif "youtu.be/" in decoded_url:
        video_id = decoded_url.split("youtu.be/")[-1].split("?")[0][:11]

    # 使用视频 ID 生成唯一文件名，避免文件复用问题
    audio_path = Path(output_dir) / f"youtube_{video_id}.mp3"

    # 下载前删除已存在的旧文件，确保不会复用旧内容
    if audio_path.exists():
        print(f"删除旧的音频文件：{audio_path}")
        audio_path.unlink()

    # 使用 --cookies-from-browser chrome 通过 YouTube 机器人验证
    # 使用 --remote-components ejs:github 下载 JS 挑战求解器
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--force-overwrites",
        "--no-playlist",
        "--no-update",
        "--extractor-retries", "5",
        "--remote-components", "ejs:github",
        "--cookies-from-browser", "chrome",
        "-o", str(audio_path),
        decoded_url
    ]
    print(f"正在下载 YouTube 视频：{decoded_url}")
    print(f"输出文件：{audio_path}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("YouTube 下载完成")

        # 验证下载结果
        if audio_path.exists():
            file_size = audio_path.stat().st_size
            print(f"音频文件大小：{file_size / 1024 / 1024:.1f} MB")
        else:
            raise RuntimeError("下载完成后音频文件不存在")
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp 下载失败：{e}")
        print(f"错误输出：{e.stderr}")
        # 下载失败时清理可能产生的部分文件
        if audio_path.exists():
            print(f"清理下载失败的文件：{audio_path}")
            audio_path.unlink()
        raise RuntimeError(f"YouTube 视频下载失败：{e.stderr}")
    except Exception as e:
        # 其他异常时也清理文件
        if audio_path.exists():
            print(f"清理异常文件：{audio_path}")
            audio_path.unlink()
        raise
    return str(audio_path)

async def download_douyin_audio(url: str, output_dir: str = "downloads") -> str:
    """使用 TikHub API 下载抖音视频音频"""
    os.makedirs(output_dir, exist_ok=True)

    # 优先从环境变量获取 API 密钥，备用从配置获取
    api_key = os.getenv('TIKHUB_API_KEY')
    if not api_key:
        from .config import config_manager
        api_key = config_manager.config.get("api_keys", {}).get("tikhub")

    # 清理抖音分享口令格式（如"6.39 03/26 14:06 [抖音] https://v.douyin.com/xxxxx/"）
    from .douyin_handler import clean_douyin_url
    cleaned_url = clean_douyin_url(url)
    print(f"抖音分享口令清理后 URL: {cleaned_url}")

    # 使用抖音处理器下载音频
    from .douyin_handler import process_douyin_url
    audio_path = process_douyin_url(cleaned_url, output_dir, api_key)
    return audio_path

async def download_audio_from_url(url: str, output_dir: str = "downloads") -> str:
    if is_douyin_url(url):
        return await download_douyin_audio(url, output_dir)
    else:
        platform = get_platform(url)
        if platform == 'bilibili':
            return await download_bilibili_audio(url, output_dir)
        elif platform == 'youtube':
            return await download_youtube_audio(url, output_dir)
        else:
            raise ValueError(f"暂不支持该平台：{url}")

def download_audio(url: str, output_dir: str = "downloads") -> str:
    return asyncio.run(download_audio_from_url(url, output_dir))
