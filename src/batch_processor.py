"""
batch_processor.py
批量处理音频文件模块
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json

from .audio_handler import handle_audio_upload
from .transcribe import transcribe_local_audio
from .summarize import summarize_text
from .utils import safe_filename
from .config import config_manager


def get_audio_files_from_dir(upload_dir: str) -> List[str]:
    """从指定目录获取所有音频文件"""
    supported_formats = ['*.mp3', '*.wav', '*.m4a', '*.mp4', '*.aac', '*.flac', '*.wma', '*.amr']
    audio_files = []
    
    for fmt in supported_formats:
        audio_files.extend(glob.glob(os.path.join(upload_dir, fmt), recursive=True))
        audio_files.extend(glob.glob(os.path.join(upload_dir, fmt.upper()), recursive=True))
    
    # 去重并按文件名排序
    unique_files = list(set(audio_files))
    return sorted(unique_files)


def process_single_audio(audio_file: str, model: str, prompt_to_use: str, language: str = None, provider: str = "deepseek") -> Dict[str, Any]:
    """处理单个音频文件"""
    # 处理音频文件
    processed_audio_path = handle_audio_upload(audio_file, output_dir="downloads")

    # 转录音频
    transcript = transcribe_local_audio(processed_audio_path, model=model, language=language, save_transcription=True)

    # 生成总结
    summary = summarize_text(transcript, prompt=prompt_to_use, model=config_manager.get_default_model(), provider=provider)

    return {
        "transcript": transcript,
        "summary": summary,
        "processed_audio_path": processed_audio_path
    }


def process_batch(upload_dir: str = "uploads", model: str = "small",
                 prompt_to_use: str = None, prompt_template: str = "default课堂笔记",
                 language: str = None, provider: str = "deepseek") -> List[Dict[str, Any]]:
    """批量处理音频文件"""
    from .prompts import prompt_templates

    # 获取实际使用的提示词
    if prompt_to_use is None:
        prompt_to_use = prompt_templates.get(prompt_template, prompt_templates["default课堂笔记"])

    # 确保上传目录存在
    Path(upload_dir).mkdir(exist_ok=True)

    # 获取所有音频文件
    audio_files = get_audio_files_from_dir(upload_dir)

    if not audio_files:
        print(f"⚠️  在 {upload_dir} 目录中未找到音频文件")
        return []

    total_files = len(audio_files)
    print(f"📁 找到 {total_files} 个音频文件")

    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"🎵 处理第 {i}/{total_files} 个文件: {os.path.basename(audio_file)}")

        try:
            # 处理单个文件
            result = process_single_audio(audio_file, model, prompt_to_use, language, provider)

            # 生成安全的文件名
            file_stem = Path(audio_file).stem
            safe_stem = safe_filename(file_stem)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存转录文本到transcriptions文件夹
            transcriptions_dir = Path("transcriptions")
            transcriptions_dir.mkdir(exist_ok=True)
            transcript_path = transcriptions_dir / f"local_{safe_stem}_{timestamp}_转录.txt"
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(result["transcript"])

            # 保存总结到summaries文件夹
            summaries_dir = Path("summaries")
            summaries_dir.mkdir(exist_ok=True)
            summary_path = summaries_dir / f"local_{safe_stem}_{timestamp}_总结.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(result["summary"])

            results.append({
                "file": audio_file,
                "status": "success",
                "transcript_path": str(transcript_path),
                "summary_path": str(summary_path),
                "error": None
            })
            print(f"✅ 第 {i} 个文件处理完成")

        except Exception as e:
            error_msg = str(e)
            results.append({
                "file": audio_file,
                "status": "error",
                "transcript_path": None,
                "summary_path": None,
                "error": error_msg
            })
            print(f"❌ 第 {i} 个文件处理失败: {error_msg}")

    # 生成批量处理报告
    generate_batch_report(results, upload_dir, model, prompt_template, language)

    return results


def generate_batch_report(results: List[Dict[str, Any]], upload_dir: str, 
                         model: str, prompt_template: str, language: str):
    """生成批量处理报告"""
    total = len(results)
    success_count = len([r for r in results if r["status"] == "success"])
    error_count = total - success_count
    
    report = {
        "batch_info": {
            "upload_dir": upload_dir,
            "total_files": total,
            "success_count": success_count,
            "error_count": error_count,
            "model": model,
            "prompt_template": prompt_template,
            "language": language,
            "timestamp": datetime.now().isoformat()
        },
        "results": results
    }
    
    # 保存JSON格式报告
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成人类可读的报告
    readable_report_path = reports_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(readable_report_path, "w", encoding="utf-8") as f:
        f.write("批量处理报告\n")
        f.write("="*50 + "\n")
        f.write(f"上传目录: {upload_dir}\n")
        f.write(f"处理时间: {report['batch_info']['timestamp']}\n")
        f.write(f"使用模型: {report['batch_info']['model']}\n")
        f.write(f"使用模板: {report['batch_info']['prompt_template']}\n")
        f.write(f"音频语言: {report['batch_info']['language'] if report['batch_info']['language'] else '自动检测'}\n")
        f.write(f"总文件数: {total}\n")
        f.write(f"成功处理: {success_count}\n")
        f.write(f"处理失败: {error_count}\n\n")
        
        f.write("详细结果:\n")
        f.write("-"*30 + "\n")
        for result in results:
            status = "✓" if result["status"] == "success" else "✗"
            f.write(f"{status} {os.path.basename(result['file'])}\n")
            if result["status"] == "error":
                f.write(f"   错误: {result['error']}\n")
            f.write("\n")
    
    print(f"\n📊 批量处理完成!")
    print(f"📈 成功: {success_count}/{total} 个文件")
    if error_count > 0:
        print(f"⚠️  失败: {error_count} 个文件")
    print(f"📋 报告已保存至: {readable_report_path}")