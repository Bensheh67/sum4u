"""
transcribe.py
Whisper 转录模块 - 使用本地 whisper 进行音频转录。
"""

import os
from typing import Optional
import tempfile
from moviepy import AudioFileClip

def transcribe_audio(audio_path: str, api_key: Optional[str] = None, model: str = "small", language: Optional[str] = None) -> str:
    """
    将音频文件转为文本，使用本地 whisper 进行转录。
    当文件大于100M时自动分段（每600秒一段）转录。
    :param audio_path: 音频文件路径
    :param api_key: 保留参数以兼容接口（实际不使用）
    :param model: whisper模型大小（tiny, base, small, medium, large），默认small
    :param language: 指定音频语言（如 'zh', 'en'），None表示自动检测
    :return: 转录文本
    """
    try:
        import whisper
        file_size = os.path.getsize(audio_path)
        MB = 1024 * 1024

        print(f"音频文件大小: {file_size/MB:.1f}MB")
        print(f"使用本地 whisper ({model}) 进行转录...")
        print("正在加载模型...")

        # 加载模型
        whisper_model = whisper.load_model(model)
        print("模型加载完成，开始转录...")

        if file_size <= 100 * MB:
            # 设置转录参数
            transcribe_kwargs = {
                "verbose": False  # 添加verbose=False避免过多输出
            }
            if language:
                transcribe_kwargs["language"] = language

            result = whisper_model.transcribe(audio_path, **transcribe_kwargs)
            print("转录完成！")
            return result["text"]
        else:
            print(f"音频文件较大，开始分段转录...")
            audio = AudioFileClip(audio_path)
            duration = int(audio.duration)  # 秒
            chunk_sec = 600  # 每段10分钟
            texts = []

            total_chunks = (duration + chunk_sec - 1) // chunk_sec  # 计算总段数
            print(f"总共需要处理 {total_chunks} 个分段")

            for i, start in enumerate(range(0, duration, chunk_sec), 1):
                end = min(start + chunk_sec, duration)
                print(f"正在处理分段 {i}/{total_chunks}: {start//60:02d}:{start%60:02d} - {end//60:02d}:{end%60:02d}")

                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as tmp:
                    # 兼容moviepy 1.x和2.x的分段方法
                    try:
                        segment = audio.subclip(start, end)
                    except AttributeError:
                        segment = audio.subclipped(start, end)

                    # 保存分段音频
                    try:
                        segment.write_audiofile(tmp.name, codec='mp3', verbose=False, logger=None)
                    except Exception as e:
                        print(f"保存分段音频失败: {e}")
                        audio.close()
                        raise e

                    # 转录分段音频
                    try:
                        # 设置转录参数
                        transcribe_kwargs = {
                            "verbose": False  # 添加verbose=False避免过多输出
                        }
                        if language:
                            transcribe_kwargs["language"] = language

                        result = whisper_model.transcribe(tmp.name, **transcribe_kwargs)
                        texts.append(result["text"])
                        print(f"分段 {i} 转录完成")
                    except Exception as e:
                        print(f"转录分段 {i} 失败: {e}")
                        audio.close()
                        raise e

            audio.close()
            print("所有分段转录完成！")
            return '\n'.join(texts)
    except ImportError:
        raise RuntimeError("未安装 whisper 库，请运行: pip install openai-whisper")
    except Exception as e:
        raise RuntimeError(f"本地 whisper 转录失败: {e}")


def transcribe_local_audio(audio_path: str, model: str = "small", language: Optional[str] = None) -> str:
    """
    专门用于转录本地音频文件的函数
    :param audio_path: 本地音频文件路径
    :param model: whisper模型大小
    :param language: 指定语言，None表示自动检测
    :return: 转录文本
    """
    return transcribe_audio(audio_path, model=model, language=language)