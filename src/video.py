"""
video.py
视频截图提取模块 - 使用 ffmpeg 提取视频关键帧。
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


SCREENSHOTS_DIR = "screenshots"


def ensure_summary_dir(summary_name: str) -> Path:
    """创建并返回总结文件夹（包含截图子目录）"""
    # 清理文件名中的非法字符
    safe_name = summary_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_')
    safe_name = safe_name.replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_')
    safe_name = safe_name.replace('|', '_').rstrip('. ')  # 不能以点或空格结尾
    safe_name = safe_name[:100] if len(safe_name) > 100 else safe_name
    dir_path = Path("summaries") / safe_name
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def ensure_screenshots_dir(summary_name: str) -> Path:
    """创建并返回截图保存目录"""
    dir_path = Path("summaries") / summary_name / SCREENSHOTS_DIR
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def extract_frame(video_path: str, timestamp: float, output_path: str, quality: int = 2) -> bool:
    """
    从视频中提取单个帧

    Args:
        video_path: 视频文件路径
        timestamp: 时间点（秒）
        output_path: 输出图片路径
        quality: 质量 (1=最高, 31=最低)

    Returns:
        是否成功提取
    """
    print(f"[DEBUG] extract_frame: timestamp={timestamp}, output={output_path}")

    if not os.path.exists(video_path):
        print(f"[ERROR] 视频文件不存在: {video_path}")
        return False

    cmd = [
        "ffmpeg",
        "-ss", str(timestamp),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", str(quality),
        "-y",
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"[ERROR] ffmpeg失败: returncode={result.returncode}")
            print(f"[ERROR] stderr: {result.stderr[:200]}")
        success = result.returncode == 0 and os.path.exists(output_path)
        print(f"[DEBUG] extract_frame结果: {success}")
        return success
    except Exception as e:
        print(f"[ERROR] extract_frame异常: {e}")
        return False


def extract_multiple_frames(
    video_path: str,
    timestamps: List[Dict],
    output_dir: Path,
    video_duration: float = None,
    prefix: str = "frame"
) -> List[Dict]:
    """
    批量提取多个关键帧

    Args:
        video_path: 视频文件路径
        timestamps: 时间点列表，每项包含 timestamp, reason, relevance
        output_dir: 输出目录
        prefix: 文件名前缀

    Returns:
        成功提取的帧信息列表
    """
    print(f"[DEBUG] extract_multiple_frames:")
    print(f"  video_path: {video_path}")
    print(f"  timestamps数量: {len(timestamps)}")
    print(f"  output_dir: {output_dir}")
    print(f"  video_duration: {video_duration}")

    extracted = []

    for i, ts_info in enumerate(timestamps):
        timestamp = ts_info["timestamp"]

        if video_duration and timestamp > video_duration:
            continue

        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = int(timestamp % 60)
        time_str = f"{hours:02d}{minutes:02d}{seconds:02d}"

        filename = f"{prefix}_{i+1:03d}_{time_str}.jpg"
        output_path = output_dir / filename

        success = extract_frame(video_path, timestamp, str(output_path))

        if success:
            extracted.append({
                "timestamp": timestamp,
                "timestamp_display": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                "filename": filename,
                "path": str(output_path),
                "reason": ts_info.get("reason", ""),
                "relevance": ts_info.get("relevance", 3)
            })

    return extracted


def get_video_duration(video_path: str) -> Optional[float]:
    """获取视频时长（秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return None
