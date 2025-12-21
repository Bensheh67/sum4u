"""
main.py
命令行主入口。
"""
import sys
import os
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "src"

import argparse
from datetime import datetime
from pathlib import Path
from .audio import download_audio
from .transcribe import transcribe_audio, transcribe_local_audio
from .summarize import summarize_text
from .prompts import prompt_templates
from .audio_handler import handle_audio_upload
from .utils import safe_filename
from .batch_processor import process_batch


def generate_filename(url_or_path: str, has_summary: bool = True, is_local: bool = False) -> str:
    """根据URL或文件路径和是否有总结生成文件名"""
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if is_local:
        # 本地文件处理
        file_stem = Path(url_or_path).stem
        # 清理文件名中的特殊字符
        safe_stem = safe_filename(file_stem)
        platform = "local"
        video_id = safe_stem[:10]  # 取前10个字符作为ID
    else:
        # 从URL中提取视频ID
        if "bilibili.com" in url_or_path:
            # B站视频ID格式：BV1xx411c7mu
            if "BV" in url_or_path:
                video_id = url_or_path.split("BV")[1].split("?")[0][:10]
                platform = "bilibili"
            else:
                video_id = "unknown"
                platform = "bilibili"
        elif "youtube.com" in url_or_path:
            # YouTube视频ID格式：dQw4w9WgXcQ
            if "v=" in url_or_path:
                video_id = url_or_path.split("v=")[1].split("&")[0][:11]
                platform = "youtube"
            else:
                video_id = "unknown"
                platform = "youtube"
        else:
            video_id = "unknown"
            platform = "other"

    # 生成文件名
    if has_summary:
        filename = f"{platform}_{video_id}_{timestamp}_总结.md"
    else:
        filename = f"{platform}_{video_id}_{timestamp}_转录.txt"

    return filename


def process_local_audio(audio_file_path: str, model: str, prompt_to_use: str, output_path: str, language: str = None):
    """处理本地音频文件的完整流程"""
    print("[1/3] 准备音频文件...")
    processed_audio_path = handle_audio_upload(audio_file_path, output_dir="downloads")
    print(f"音频已准备: {processed_audio_path}")

    print(f"[2/3] 转录音频 (使用模型: {model})...")
    print("提示：转录过程可能需要几分钟时间，请耐心等待...")
    transcript = transcribe_local_audio(processed_audio_path, model=model, language=language)
    print("转录完成！")

    print("[3/3] 结构化总结...")
    summary = summarize_text(transcript, prompt=prompt_to_use)
    print("摘要完成！")

    # 保存到总结文件夹
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"结果已保存到: {output_path}")


def process_video_url(video_url: str, model: str, prompt_to_use: str, output_path: str):
    """处理视频URL的完整流程"""
    print("[1/3] 下载并提取音频...")
    audio_path = download_audio(video_url)
    print(f"音频已保存: {audio_path}")

    print(f"[2/3] 转录音频 (使用模型: {model})...")
    print("提示：转录过程可能需要几分钟时间，请耐心等待...")
    transcript = transcribe_audio(audio_path, model=model)
    print("转录完成！")

    print("[3/3] 结构化总结...")
    summary = summarize_text(transcript, prompt=prompt_to_use)
    print("摘要完成！")

    # 保存到总结文件夹
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"结果已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="音频/视频结构化总结工具")

    # 添加互斥组，确保用户只能提供URL或本地文件之一，或者进行批量处理
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--url", help="视频链接（支持B站、YouTube等）")
    group.add_argument("--audio-file", help="本地音频文件路径（支持MP3, WAV, M4A等格式）")
    group.add_argument("--batch", action="store_true", help="批量处理上传文件夹中的所有音频文件")

    parser.add_argument("--upload-dir", required=False, default="uploads", help="批量处理的上传文件夹路径，默认为uploads")
    parser.add_argument("--model", required=False, default="small", help="Whisper模型大小 (tiny, base, small, medium, large-v1, large-v2, large-v3)，默认small")
    parser.add_argument("--output", required=False, help="自定义输出文件名（单文件处理时有效）")
    parser.add_argument("--prompt", required=False, help="自定义摘要提示词")
    parser.add_argument("--prompt_template", required=False, default="default课堂笔记", help="选择摘要提示词模板，可选: default课堂笔记, youtube_英文笔记, youtube_结构化提取, youtube_精炼提取, youtube_专业课笔记, 爆款短视频文案, youtube_视频总结")
    parser.add_argument("--language", required=False, help="指定音频语言（如 zh, en），不指定则自动检测")

    args = parser.parse_args()

    # 如果没有提供任何参数，则显示帮助信息
    if not args.url and not args.audio_file and not args.batch:
        parser.print_help()
        sys.exit(1)

    # 创建必要的文件夹
    summaries_dir = Path("summaries")
    summaries_dir.mkdir(exist_ok=True)
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    transcriptions_dir = Path("transcriptions")
    transcriptions_dir.mkdir(exist_ok=True)

    # 优先使用 --prompt，如果没有则用模板
    prompt_to_use = args.prompt if args.prompt else prompt_templates.get(args.prompt_template, prompt_templates["default课堂笔记"])

    # 根据输入类型决定处理流程
    if args.url:
        # 处理URL
        print(f"处理视频URL: {args.url}")

        # 生成自动文件名
        auto_filename = generate_filename(args.url, has_summary=True, is_local=False)

        # 使用自定义文件名或自动生成的文件名
        if args.output:
            output_path = summaries_dir / args.output
        else:
            output_path = summaries_dir / auto_filename

        process_video_url(args.url, args.model, prompt_to_use, output_path)

    elif args.audio_file:
        # 处理本地音频文件
        print(f"处理本地音频文件: {args.audio_file}")

        # 验证文件是否存在
        if not Path(args.audio_file).exists():
            print(f"错误: 音频文件不存在: {args.audio_file}")
            sys.exit(1)

        # 生成自动文件名
        auto_filename = generate_filename(args.audio_file, has_summary=True, is_local=True)

        # 使用自定义文件名或自动生成的文件名
        if args.output:
            output_path = summaries_dir / args.output
        else:
            output_path = summaries_dir / auto_filename

        process_local_audio(args.audio_file, args.model, prompt_to_use, output_path, args.language)

    elif args.batch:
        # 批量处理模式
        print(f"批量处理模式: 处理 {args.upload_dir} 文件夹中的所有音频文件")
        process_batch(
            upload_dir=args.upload_dir,
            model=args.model,
            prompt_to_use=prompt_to_use,
            prompt_template=args.prompt_template,
            language=args.language
        )


if __name__ == "__main__":
    main()