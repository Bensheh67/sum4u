"""
audio_handler.py
处理本地音频文件上传和格式转换。
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from utils import safe_filename


def validate_audio_file(file_path: str) -> bool:
    """
    验证音频文件格式是否支持
    :param file_path: 音频文件路径
    :return: 是否支持该格式
    """
    supported_formats = {'.mp3', '.wav', '.m4a', '.mp4', '.aac', '.flac', '.wma', '.amr'}
    file_ext = Path(file_path).suffix.lower()
    return file_ext in supported_formats


def copy_audio_to_downloads(file_path: str, output_dir: str = "downloads") -> str:
    """
    将音频文件复制到downloads目录并返回新的路径
    :param file_path: 原始音频文件路径
    :param output_dir: 输出目录
    :return: 复制后的音频文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取原始文件信息
    original_path = Path(file_path)
    filename = original_path.name
    
    # 创建安全的文件名
    safe_name = safe_filename(filename)
    
    # 确保输出路径在downloads目录中
    output_path = Path(output_dir) / safe_name
    
    # 如果目标文件已存在，则添加序号
    counter = 1
    original_output_path = output_path
    while output_path.exists():
        stem = original_output_path.stem
        suffix = original_output_path.suffix
        output_path = Path(output_dir) / f"{stem}_{counter}{suffix}"
        counter += 1
    
    # 复制文件
    shutil.copy2(file_path, output_path)
    
    return str(output_path)


def convert_audio_format(input_path: str, output_path: str, target_format: str = ".mp3") -> str:
    """
    转换音频文件格式
    :param input_path: 输入音频文件路径
    :param output_path: 输出音频文件路径
    :param target_format: 目标格式
    :return: 转换后的音频文件路径
    """
    try:
        # 尝试导入moviepy 2.x版本的模块
        try:
            from moviepy import AudioFileClip
        except ImportError:
            from moviepy.editor import AudioFileClip

        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入音频文件不存在: {input_path}")

        # 使用moviepy进行格式转换
        audio_clip = AudioFileClip(input_path)

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        # 导出为指定格式
        if target_format.lower() == ".mp3":
            audio_clip.write_audiofile(output_path, logger=None)
        elif target_format.lower() == ".wav":
            audio_clip.write_audiofile(output_path, logger=None)
        else:
            # 默认转换为mp3
            output_path = output_path.rsplit('.', 1)[0] + ".mp3"
            audio_clip.write_audiofile(output_path, logger=None)

        # 关闭音频剪辑
        audio_clip.close()

        return output_path
    except ImportError:
        # 检查moviepy是否已安装
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "show", "moviepy"])
        except subprocess.CalledProcessError:
            print("检测到moviepy未安装，正在尝试安装...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy"])
                print("moviepy安装成功！")
                # 重新导入并执行 - 兼容不同版本的moviepy
                try:
                    from moviepy import AudioFileClip
                except ImportError:
                    from moviepy.editor import AudioFileClip
                audio_clip = AudioFileClip(input_path)
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)
                if target_format.lower() == ".mp3":
                    audio_clip.write_audiofile(output_path, logger=None)
                elif target_format.lower() == ".wav":
                    audio_clip.write_audiofile(output_path, logger=None)
                else:
                    output_path = output_path.rsplit('.', 1)[0] + ".mp3"
                    audio_clip.write_audiofile(output_path, logger=None)
                audio_clip.close()
                return output_path
            except Exception as install_error:
                raise ImportError("自动安装moviepy失败，请手动运行 'pip install moviepy' 安装依赖。") from install_error
        else:
            raise ImportError("moviepy已安装但无法导入，可能存在版本兼容性问题。请尝试重新安装：'pip install --force-reinstall moviepy'。")
    except Exception as e:
        raise RuntimeError(f"音频格式转换失败: {e}")


def handle_audio_upload(file_path: str, output_dir: str = "downloads", force_convert: bool = False) -> str:
    """
    处理音频文件上传流程
    :param file_path: 上传的音频文件路径
    :param output_dir: 输出目录
    :param force_convert: 是否强制转换为MP3格式
    :return: 处理后的音频文件路径
    """
    # 验证文件格式
    if not validate_audio_file(file_path):
        supported_formats = ['.mp3', '.wav', '.m4a', '.mp4', '.aac', '.flac', '.wma', '.amr']
        raise ValueError(f"不支持的音频格式。支持的格式: {', '.join(supported_formats)}")
    
    # 复制文件到downloads目录
    copied_path = copy_audio_to_downloads(file_path, output_dir)
    
    # 检查是否需要转换格式
    if force_convert or Path(copied_path).suffix.lower() != ".mp3":
        converted_path = copied_path.rsplit('.', 1)[0] + ".mp3"
        converted_path = convert_audio_format(copied_path, converted_path)
        return converted_path
    else:
        return copied_path