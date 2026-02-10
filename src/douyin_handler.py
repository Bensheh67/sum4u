"""
douyin_handler.py
负责处理抖音视频链接，使用TikHub API下载视频音频。
"""

import os
import re
import requests
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import subprocess
from .utils import safe_filename
from .config import config_manager


def is_douyin_url(url: str) -> bool:
    """
    判断是否为抖音/TikTok/Bilibili链接
    """
    url_lower = url.lower()
    return (
        'douyin.com' in url_lower or
        'tiktok.com' in url_lower or
        'v.douyin.com' in url_lower or
        'vm.tiktok.com' in url_lower or
        'vt.tiktok.com' in url_lower
    )


def clean_douyin_url(url: str) -> str:
    """
    清理抖音URL，移除多余的参数和格式化，从分享文本中提取URL
    """
    # 移除抖音分享口令等多余内容
    # 匹配抖音分享链接格式
    dy_pattern = r'(https?://[^\s\'\"]*douyin\.com[^\s\'\"]*)'
    vm_pattern = r'(https?://[^\s\'\"]*v\.douyin\.com[^\s\'\"]*)'
    tiktok_pattern = r'(https?://[^\s\'\"]*tiktok\.com[^\s\'\"]*)'
    vm_tiktok_pattern = r'(https?://[^\s\'\"]*vm\.tiktok\.com[^\s\'\"]*)'
    vt_tiktok_pattern = r'(https?://[^\s\'\"]*vt\.tiktok\.com[^\s\'\"]*)'

    patterns = [dy_pattern, vm_pattern, tiktok_pattern, vm_tiktok_pattern, vt_tiktok_pattern]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            extracted_url = match.group(1)
            # 进一步清理URL，移除可能的尾随字符
            extracted_url = extracted_url.split()[0]  # 取第一个URL
            extracted_url = extracted_url.split('|')[0]  # 取第一部分
            return extracted_url.strip()

    # 如果没匹配到，返回原始URL
    return url


def get_douyin_video_data(video_url: str, api_key: str = None) -> dict:
    """
    通过TikHub API获取抖音视频数据
    """
    # 如果没有提供API密钥，则从环境变量或配置中获取
    if api_key is None:
        api_key = os.getenv('TIKHUB_API_KEY')  # 优先从环境变量获取
        if not api_key:
            api_key = config_manager.config.get("api_keys", {}).get("tikhub")  # 备用从配置获取
    
    if not api_key:
        raise ValueError("未配置TikHub API密钥，请设置环境变量TIKHUB_API_KEY或在API配置中设置")

    # 使用TikHub抖音App V3 API端点 - 根据分享链接获取视频数据
    api_url = "https://api.tikhub.io/api/v1/douyin/app/v3/fetch_one_video_by_share_url"

    # 准备请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # 准备请求参数（GET请求参数）
    params = {
        "share_url": video_url  # 使用原始URL，API会自动处理分享链接
    }

    try:
        print(f"正在调用TikHub抖音App V3 API获取视频信息: {api_url}")
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # 检查API响应是否成功
        if response.status_code != 200 or data.get("code") != 200:
            error_msg = data.get('message', f'API返回错误，状态码: {response.status_code}')
            print(f"TikHub API返回错误: {error_msg}")
            raise ValueError(f"TikHub API返回错误: {error_msg}")

        return data
    except requests.exceptions.RequestException as e:
        print(f"获取抖音视频数据失败: {e}")
        raise
    except ValueError as e:
        print(f"解析抖音视频数据失败: {e}")
        raise
    except Exception as e:
        print(f"获取抖音视频数据时发生未知错误: {e}")
        raise


def download_douyin_video(video_url: str, output_dir: str = "downloads", api_key: str = None) -> str:
    """
    使用TikHub API下载抖音视频，提取音频
    """
    os.makedirs(output_dir, exist_ok=True)

    # 获取视频数据
    print(f"正在获取抖音视频信息: {video_url}")
    video_data = get_douyin_video_data(video_url, api_key)

    # 提取视频下载链接
    video_url_direct = None

    # 根据TikHub抖音App V3 API响应格式提取视频URL
    if 'data' in video_data:
        data = video_data['data']

        # TikHub抖音App V3 API响应格式通常在 data.aweme_detail.video 中
        if 'aweme_detail' in data:
            aweme_detail = data['aweme_detail']
            
            # 检查视频播放地址
            if 'video' in aweme_detail:
                video_info = aweme_detail['video']

                # 优先级：play_addr > download_addr > bit_rate_list > play_url
                # 在抖音API中，play_addr通常包含无水印视频链接
                if 'play_addr' in video_info:
                    play_addr_info = video_info['play_addr']
                    if 'url_list' in play_addr_info and play_addr_info['url_list']:
                        # 通常第一个URL是最高质量的
                        video_url_direct = play_addr_info['url_list'][0]
                elif 'download_addr' in video_info:
                    download_addr_info = video_info['download_addr']
                    if 'url_list' in download_addr_info and download_addr_info['url_list']:
                        video_url_direct = download_addr_info['url_list'][0]
                elif 'bit_rate' in video_info and len(video_info['bit_rate']) > 0:
                    # 如果有多个比特率选项，选择第一个（通常是最高质量）
                    first_bitrate = video_info['bit_rate'][0]
                    if 'play_addr' in first_bitrate and 'url_list' in first_bitrate['play_addr']:
                        video_url_direct = first_bitrate['play_addr']['url_list'][0]
                elif 'play_url' in video_info:
                    play_url_info = video_info['play_url']
                    if 'url_list' in play_url_info and play_url_info['url_list']:
                        video_url_direct = play_url_info['url_list'][0]
        # 尝试其他可能的结构
        elif 'video' in data:
            video_obj = data['video']
            
            if 'play_addr' in video_obj:
                play_addr_info = video_obj['play_addr']
                if 'url_list' in play_addr_info and play_addr_info['url_list']:
                    video_url_direct = play_addr_info['url_list'][0]
            elif 'download_addr' in video_obj:
                download_addr_info = video_obj['download_addr']
                if 'url_list' in download_addr_info and download_addr_info['url_list']:
                    video_url_direct = download_addr_info['url_list'][0]
            elif 'play_url' in video_obj:
                play_url_info = video_obj['play_url']
                if 'url_list' in play_url_info and play_url_info['url_list']:
                    video_url_direct = play_url_info['url_list'][0]
        # TikHub API也可能直接返回视频URL
        elif 'video_url' in data:
            video_url_direct = data['video_url']
        elif 'play_url' in data:
            video_url_direct = data['play_url']

    if not video_url_direct:
        raise ValueError(f"未能从API响应中获取视频下载链接: {video_data}")

    # 下载视频
    print(f"获取到视频下载链接，开始下载: {video_url_direct[:50]}...")
    temp_video_path = os.path.join(output_dir, f"douyin_temp_{abs(hash(video_url)) % 10000}.mp4")

    # 下载视频
    response = requests.get(video_url_direct, stream=True, timeout=60)
    response.raise_for_status()

    with open(temp_video_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"视频下载完成: {temp_video_path}")

    # 提取音频
    print("正在提取音频...")
    audio_path = os.path.join(output_dir, f"douyin_{abs(hash(video_url)) % 10000}.mp3")

    # 使用ffmpeg提取音频
    cmd = [
        "ffmpeg",
        "-i", temp_video_path,
        "-vn",  # 不包含视频
        "-acodec", "mp3",  # 音频编码为mp3
        "-ar", "44100",  # 音频采样率
        "-ac", "2",  # 音频通道数
        "-b:a", "192k",  # 音频比特率
        "-y",  # 覆盖输出文件
        audio_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"音频提取失败: {result.stderr}")
        # 删除临时视频文件
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        raise RuntimeError(f"音频提取失败: {result.stderr}")

    print(f"音频提取完成: {audio_path}")

    # 删除临时视频文件
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)

    return audio_path


def process_douyin_url(url: str, output_dir: str = "downloads", api_key: str = None) -> str:
    """
    处理抖音URL的主函数
    """
    if not is_douyin_url(url):
        raise ValueError(f"不是有效的抖音/TikTok链接: {url}")

    return download_douyin_video(url, output_dir, api_key)


def batch_process_douyin_urls(urls: list, output_dir: str = "downloads", api_key: str = None) -> list:
    """
    批量处理抖音URL的函数
    """
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"正在处理第 {i}/{len(urls)} 个视频: {url[:50]}...")
        try:
            # 清理URL
            cleaned_url = clean_douyin_url(url)
            print(f"  清理后URL: {cleaned_url}")
            
            # 处理单个URL
            audio_path = process_douyin_url(cleaned_url, output_dir, api_key)
            results.append({
                "url": url,
                "cleaned_url": cleaned_url,
                "audio_path": audio_path,
                "status": "success"
            })
            print(f"  ✓ 成功: {audio_path}")
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ 失败: {error_msg}")
            results.append({
                "url": url,
                "cleaned_url": clean_douyin_url(url) if is_douyin_url(url) else url,
                "audio_path": None,
                "status": "error",
                "error": error_msg
            })
    
    return results