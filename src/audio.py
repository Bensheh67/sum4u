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
        video_id = url.split("BV")[1].split("?")[0].rstrip("/")[:12]
    elif "/video/" in url:
        video_id = url.split("/video/")[-1].split("?")[0].rstrip("/")[:12]

    # 使用不含扩展名的模板，让 yt-dlp 自动处理扩展名
    audio_template = Path(output_dir) / f"bilibili_{video_id}"

    try:
        # 使用 yt-dlp 下载 Bilibili 视频并提取音频
        # 修复 URL 中的转义字符
        import urllib.parse
        decoded_url = urllib.parse.unquote(url)

        # 额外处理：去除可能的双反斜杠转义
        import re
        decoded_url = re.sub(r'\\\\', r'\\', decoded_url)  # 将双反斜杠替换为单反斜杠
        decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

        # 删除该视频相关的旧文件
        for old_file in Path(output_dir).glob(f"bilibili_{video_id}*"):
            if old_file.is_file():
                print(f"删除旧文件：{old_file}")
                old_file.unlink()

        cmd = [
            "yt-dlp",
            "-x",  # 提取音频
            "--audio-format", "mp3",  # 转换为 mp3
            "--audio-quality", "0",  # 最高音质
            "--force-overwrites",  # 强制覆盖已存在的文件
            "--no-update",  # 不检查更新
            "--extractor-retries", "5",  # 提取器重试次数
            "-o", str(audio_template) + ".%(ext)s",  # 输出模板
            decoded_url
        ]

        print(f"正在下载 Bilibili 视频：{decoded_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Bilibili 下载完成")

        # 验证下载结果 - 查找生成的文件
        downloaded_files = list(Path(output_dir).glob(f"bilibili_{video_id}*.mp3"))
        if downloaded_files:
            # 选最新的文件
            audio_path = max(downloaded_files, key=lambda p: p.stat().st_mtime)
            file_size = audio_path.stat().st_size
            print(f"音频文件：{audio_path} ({file_size / 1024 / 1024:.1f} MB)")
        else:
            # 如果没找到 mp3，查找任何 bilibili_{video_id} 开头的文件
            any_files = list(Path(output_dir).glob(f"bilibili_{video_id}*"))
            if any_files:
                audio_path = max(any_files, key=lambda p: p.stat().st_mtime)
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

def download_audio(url: str, output_dir: str = "downloads") -> tuple[str, str]:
    """
    下载音频并返回 (音频路径, 视频标题)

    Returns:
        (音频文件路径, 视频标题)
    """
    result = asyncio.run(download_audio_from_url(url, output_dir))
    # 获取视频标题
    title = get_video_title(url)
    return result, title


def get_video_title(url: str) -> str:
    """
    使用 yt-dlp 获取视频标题

    Returns:
        视频标题
    """
    import urllib.parse
    import re
    import subprocess

    # 清理 URL
    decoded_url = urllib.parse.unquote(url)
    decoded_url = re.sub(r'\\\\', r'\\', decoded_url)
    decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

    try:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--print", "%(title)s",
            "--no-warnings",
            "-o", "%(title)s",
            decoded_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            title = result.stdout.strip()
            # 清理标题中的非法字符
            title = re.sub(r'[<>:"/\\|?*]', '_', title)
            title = title[:100]  # 限制长度
            return title if title else "视频总结"
    except Exception as e:
        print(f"获取视频标题失败: {e}")
    return "视频总结"


def download_video(url: str, output_dir: str = "downloads") -> tuple[str, str]:
    """
    下载完整视频（不提取音频），用于截图提取

    Returns:
        (视频文件路径, 视频标题)
    """
    import urllib.parse
    import re

    os.makedirs(output_dir, exist_ok=True)

    # 获取视频标题
    title = get_video_title(url)

    if is_douyin_url(url):
        video_path = asyncio.run(_download_douyin_video(url, output_dir))
        return video_path, title

    decoded_url = urllib.parse.unquote(url)
    decoded_url = re.sub(r'\\\\', r'\\', decoded_url)
    decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

    platform = get_platform(url)

    if platform == 'youtube':
        video_path = asyncio.run(_download_youtube_video(url, output_dir))
        return video_path, title
    elif platform == 'bilibili':
        video_path = asyncio.run(_download_bilibili_video(url, output_dir))
        return video_path, title
    else:
        raise ValueError(f"暂不支持该平台的视频下载：{url}")


async def _download_youtube_video(url: str, output_dir: str) -> str:
    """下载 YouTube 视频"""
    import urllib.parse
    import re

    decoded_url = urllib.parse.unquote(url)
    decoded_url = re.sub(r'\\\\', r'\\', decoded_url)
    decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

    video_id = "unknown"
    if "v=" in decoded_url:
        video_id = decoded_url.split("v=")[1].split("&")[0][:11]
    elif "youtu.be/" in decoded_url:
        video_id = decoded_url.split("youtu.be/")[-1].split("?")[0][:11]

    video_path = Path(output_dir) / f"youtube_{video_id}.mp4"

    # 删除旧文件确保重新下载
    if video_path.exists():
        print(f"删除旧视频文件：{video_path}")
        video_path.unlink()

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]",
        "--merge-output-format", "mp4",
        "--force-overwrites",
        "--no-update",
        "--extractor-retries", "5",
        "--cookies-from-browser", "chrome",
        "-o", str(video_path),
        decoded_url
    ]

    print(f"正在下载 YouTube 视频：{decoded_url}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("YouTube 视频下载完成")
    return str(video_path)


async def _download_bilibili_video(url: str, output_dir: str) -> str:
    """下载 Bilibili 视频"""
    import urllib.parse
    import re

    decoded_url = urllib.parse.unquote(url)
    decoded_url = re.sub(r'\\\\', r'\\', decoded_url)
    decoded_url = decoded_url.replace('\\?', '?').replace('\\&', '&').replace('\\=', '=')

    video_id = "unknown"
    if "BV" in url:
        video_id = url.split("BV")[1].split("?")[0].rstrip("/")[:12]
    elif "/video/" in url:
        video_id = url.split("/video/")[-1].split("?")[0].rstrip("/")[:12]

    video_path = Path(output_dir) / f"bilibili_{video_id}.mp4"

    # 删除旧文件确保重新下载
    if video_path.exists():
        print(f"删除旧视频文件：{video_path}")
        video_path.unlink()

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]",
        "--merge-output-format", "mp4",
        "--force-overwrites",
        "--no-update",
        "--extractor-retries", "5",
        "-o", str(video_path),
        decoded_url
    ]

    print(f"正在下载 Bilibili 视频：{decoded_url}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    print("Bilibili 视频下载完成")
    return str(video_path)


async def _download_douyin_video(url: str, output_dir: str) -> str:
    """下载抖音视频"""
    from .douyin_handler import get_douyin_video_data, clean_douyin_url

    api_key = os.getenv('TIKHUB_API_KEY')
    if not api_key:
        from .config import config_manager
        api_key = config_manager.config.get("api_keys", {}).get("tikhub")

    cleaned_url = clean_douyin_url(url)
    video_data = get_douyin_video_data(cleaned_url, api_key)

    video_url = None
    if 'original_video_url' in video_data:
        video_url = video_data['original_video_url']
    elif 'data' in video_data:
        data = video_data['data']
        if 'aweme_detail' in data:
            video_info = data['aweme_detail'].get('video', {})
            if 'play_addr' in video_info:
                video_url = video_info['play_addr']['url_list'][0]

    if not video_url:
        raise ValueError("无法获取抖音视频下载链接")

    video_id = abs(hash(url)) % 10000
    video_path = Path(output_dir) / f"douyin_{video_id}.mp4"

    # 删除旧文件确保重新下载
    if video_path.exists():
        print(f"删除旧视频文件：{video_path}")
        video_path.unlink()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.douyin.com/",
    }

    session = __import__('requests').Session()
    session.trust_env = False
    session.headers.update(headers)

    print("正在下载抖音视频...")
    response = session.get(video_url, stream=True, timeout=180)
    response.raise_for_status()

    with open(video_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=512*1024):
            if chunk:
                f.write(chunk)

    print(f"抖音视频下载完成：{video_path}")
    return str(video_path)
