"""
webui.py
FastAPI Web界面后端。
"""
import os
import sys
from pathlib import Path
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import threading
import time
from datetime import datetime

# 添加src目录到Python路径
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_dir)

# 使用绝对导入
from src.audio import download_audio, download_video
from src.transcribe import transcribe_audio, transcribe_local_audio
from src.summarize import summarize_text, summarize_with_screenshots
from src.prompts import prompt_templates
from src.audio_handler import handle_audio_upload
from src.utils import safe_filename, generate_filename
from src.batch_processor import process_batch
from src.douyin_handler import is_douyin_url, clean_douyin_url
from src.config import config_manager

app = FastAPI(title="音频/视频总结工具 Web UI", version="1.0.0")

# 创建必要的目录
os.makedirs("downloads", exist_ok=True)
os.makedirs("summaries", exist_ok=True)
os.makedirs("transcriptions", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# 模拟任务状态存储
task_status = {}

# 任务历史记录
task_history = []


def process_local_audio_task(task_id: str, audio_file_path: str, model: str, prompt_to_use: str, output_path: str, language: str = None):
    """处理本地音频文件的后台任务"""
    # 记录任务开始时间
    start_time = datetime.now()

    # 添加任务到历史记录
    task_info = {
        "task_id": task_id,
        "type": "local_audio",
        "input": audio_file_path,
        "model": model,
        "prompt_template_used": prompt_to_use[:50] + "..." if len(prompt_to_use) > 50 else prompt_to_use,  # 只保存前50个字符
        "language": language,
        "start_time": start_time,
        "end_time": None,
        "status": "processing",
        "result_path": None
    }
    task_history.append(task_info)

    try:
        task_status[task_id] = {"status": "processing", "progress": 5, "message": "正在验证音频文件..."}

        print(f"[{task_id}] 验证音频文件: {audio_file_path}")
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")

        task_status[task_id] = {"status": "processing", "progress": 10, "message": "准备音频文件..."}

        print(f"[{task_id}] 准备音频文件...")
        processed_audio_path = handle_audio_upload(audio_file_path, output_dir="downloads")
        print(f"[{task_id}] 音频已准备: {processed_audio_path}")
        task_status[task_id] = {"status": "processing", "progress": 20, "message": "开始转录..."}

        print(f"[{task_id}] 转录音频 (使用模型: {model})...")
        print(f"[{task_id}] 提示：转录过程可能需要几分钟时间，请耐心等待...")
        transcript = transcribe_local_audio(processed_audio_path, model=model, language=language)
        print(f"[{task_id}] 转录完成！")
        task_status[task_id] = {"status": "processing", "progress": 70, "message": "生成AI总结..."}

        print(f"[{task_id}] 结构化总结...")
        summary = summarize_text(transcript, prompt=prompt_to_use)
        print(f"[{task_id}] 摘要完成！")
        task_status[task_id] = {"status": "processing", "progress": 90, "message": "保存结果..."}

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 保存到总结文件夹
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"[{task_id}] 结果已保存到: {output_path}")

        # 更新任务历史记录
        task_info["end_time"] = datetime.now()
        task_info["status"] = "completed"
        task_info["result_path"] = output_path

        task_status[task_id] = {"status": "completed", "progress": 100, "message": "处理完成！", "result_path": output_path}
    except Exception as e:
        # 更新任务历史记录
        task_info["end_time"] = datetime.now()
        task_info["status"] = "error"
        task_info["error"] = str(e)

        task_status[task_id] = {"status": "error", "progress": 0, "message": f"处理失败: {str(e)}", "error": str(e)}
        print(f"[{task_id}] 处理失败: {str(e)}")


def process_video_url_task(task_id: str, video_url: str, model: str, prompt_to_use: str, output_path: str, with_screenshots: bool = False):
    """处理视频URL的后台任务"""
    # 记录任务开始时间
    start_time = datetime.now()

    # 添加任务到历史记录
    task_info = {
        "task_id": task_id,
        "type": "video_url",
        "input": video_url,
        "model": model,
        "prompt_template_used": prompt_to_use[:50] + "..." if len(prompt_to_use) > 50 else prompt_to_use,  # 只保存前50个字符
        "language": None,
        "with_screenshots": with_screenshots,
        "start_time": start_time,
        "end_time": None,
        "status": "processing",
        "result_path": None
    }
    task_history.append(task_info)

    try:
        task_status[task_id] = {"status": "processing", "progress": 5, "message": "正在验证视频 URL..."}

        print(f"[{task_id}] 验证视频 URL: {video_url}")

        # 处理抖音分享口令格式（如"6.39 03/26 14:06 [抖音] https://v.douyin.com/xxxxx/"）
        if is_douyin_url(video_url):
            cleaned_url = clean_douyin_url(video_url)
            print(f"[{task_id}] 抖音分享口令，清理后 URL: {cleaned_url}")
            video_url = cleaned_url

        # 验证 URL 格式
        if not video_url or not (video_url.startswith('http://') or video_url.startswith('https://')):
            raise ValueError("无效的视频 URL")

        if with_screenshots:
            # 带截图的流程
            task_status[task_id] = {"status": "processing", "progress": 5, "message": "下载视频..."}

            try:
                print(f"[{task_id}] 下载视频...")
                print(f"[DEBUG] 调用 download_video, URL: {video_url}")
                video_path, video_title = download_video(video_url)
                print(f"[DEBUG] download_video 返回: video_path={video_path}, video_title={video_title}")
                print(f"[{task_id}] 视频已保存: {video_path}")
                print(f"[{task_id}] 视频标题: {video_title}")

                # 验证视频文件是否存在
                import os
                if os.path.exists(video_path):
                    print(f"[DEBUG] 视频文件存在: {video_path}")
                else:
                    print(f"[ERROR] 视频文件不存在: {video_path}")
            except Exception as e:
                print(f"[ERROR] download_video 异常: {e}")
                video_path = None
                video_title = video_title if 'video_title' in locals() else "视频总结"
            task_status[task_id] = {"status": "processing", "progress": 15, "message": "提取音频..."}

            print(f"[{task_id}] 提取音频...")
            audio_path, _ = download_audio(video_url)
            print(f"[{task_id}] 音频已保存: {audio_path}")
            task_status[task_id] = {"status": "processing", "progress": 25, "message": "开始转录..."}

            print(f"[{task_id}] 转录音频 (使用模型: {model})...")
            print(f"[{task_id}] 提示：转录过程可能需要几分钟时间，请耐心等待...")
            transcript, segments = transcribe_audio(audio_path, model=model, return_timestamps=True)
            print(f"[{task_id}] 转录完成！")
            task_status[task_id] = {"status": "processing", "progress": 60, "message": "生成AI总结（含截图）..."}

            print(f"[{task_id}] 生成带截图的总结...")
            summary_result = summarize_with_screenshots(
                transcript_data={"text": transcript, "segments": segments},
                video_path=video_path,
                summary_name=video_title,
                prompt=prompt_to_use,
                video_title=video_title
            )

            # 处理视频文件不存在的情况
            if summary_result[0] is None:
                print(f"[{task_id}] 视频文件不存在，无法提取截图，回退到纯文本总结...")
                # 回退到不带截图的总结
                summary = summarize_text(transcript, prompt=prompt_to_use, video_title=video_title)
                frames = []
                # 保存到文件夹内的 summary.md
                summary_dir = Path("summaries") / video_title
                summary_dir.mkdir(parents=True, exist_ok=True)
                summary_file_path = summary_dir / "summary.md"
                result_path = str(summary_dir)
            else:
                summary, frames, summary_dir = summary_result
                print(f"[{task_id}] 已提取 {len(frames)} 张截图")
                print(f"[{task_id}] 摘要完成！")
                # 保存到文件夹内的 summary.md
                summary_file_path = summary_dir / "summary.md"
                result_path = str(summary_dir)
        else:
            # 不带截图的流程
            task_status[task_id] = {"status": "processing", "progress": 10, "message": "下载并提取音频..."}

            print(f"[{task_id}] 下载并提取音频...")
            audio_path, video_title = download_audio(video_url)
            print(f"[{task_id}] 音频已保存: {audio_path}")
            print(f"[{task_id}] 视频标题: {video_title}")
            task_status[task_id] = {"status": "processing", "progress": 20, "message": "开始转录..."}

            print(f"[{task_id}] 转录音频 (使用模型: {model})...")
            print(f"[{task_id}] 提示：转录过程可能需要几分钟时间，请耐心等待...")
            transcript = transcribe_audio(audio_path, model=model)
            print(f"[{task_id}] 转录完成！")
            task_status[task_id] = {"status": "processing", "progress": 70, "message": "生成AI总结..."}

            print(f"[{task_id}] 结构化总结...")
            summary = summarize_text(transcript, prompt=prompt_to_use, video_title=video_title)
            print(f"[{task_id}] 摘要完成！")
            # 使用视频标题命名
            safe_title = video_title.replace('/', '_').replace('\\', '_')
            summary_file_path = os.path.join("summaries", f"{safe_title}_总结.md")
            result_path = summary_file_path

        task_status[task_id] = {"status": "processing", "progress": 90, "message": "保存结果..."}

        # 确保输出目录存在
        os.makedirs(os.path.dirname(summary_file_path) if os.path.dirname(summary_file_path) else ".", exist_ok=True)

        # 保存到总结文件
        with open(summary_file_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"[{task_id}] 结果已保存到: {summary_file_path}")

        # 更新任务历史记录
        task_info["end_time"] = datetime.now()
        task_info["status"] = "completed"
        task_info["result_path"] = result_path

        task_status[task_id] = {"status": "completed", "progress": 100, "message": "处理完成！", "result_path": result_path}
    except Exception as e:
        # 更新任务历史记录
        task_info["end_time"] = datetime.now()
        task_info["status"] = "error"
        task_info["error"] = str(e)

        task_status[task_id] = {"status": "error", "progress": 0, "message": f"处理失败: {str(e)}", "error": str(e)}
        print(f"[{task_id}] 处理失败: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Summary4U</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0a0f;
            --surface: #12121a;
            --surface-2: #1a1a24;
            --primary: #00ff9f;
            --primary-dim: #00cc7f;
            --secondary: #00d4ff;
            --accent: #ff00aa;
            --text: #e0e0e0;
            --muted: #666680;
            --border: #2a2a3a;
            --glow: 0 0 20px rgba(0, 255, 159, 0.3);
            --glow-strong: 0 0 30px rgba(0, 255, 159, 0.5), 0 0 60px rgba(0, 255, 159, 0.2);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                linear-gradient(rgba(0, 255, 159, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 159, 0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
        }

        body::after {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 0, 0, 0.1) 2px,
                rgba(0, 0, 0, 0.1) 4px
            );
            pointer-events: none;
            z-index: 1;
            animation: scanlines 8s linear infinite;
        }

        @keyframes scanlines {
            0% { transform: translateY(0); }
            100% { transform: translateY(4px); }
        }

        .app {
            max-width: 720px;
            margin: 0 auto;
            padding: 48px 20px 80px;
            position: relative;
            z-index: 2;
        }

        .header {
            text-align: center;
            margin-bottom: 48px;
            position: relative;
        }

        .logo {
            display: inline-flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }

        .logo-icon {
            width: 48px;
            height: 48px;
            position: relative;
        }

        .logo-icon svg {
            width: 100%;
            height: 100%;
            stroke: var(--primary);
            filter: drop-shadow(var(--glow));
        }

        .logo-text {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            color: var(--primary);
            text-shadow: var(--glow-strong);
            letter-spacing: 0.1em;
        }

        .tagline {
            font-size: 0.75rem;
            color: var(--muted);
            letter-spacing: 0.3em;
            text-transform: uppercase;
        }

        .tabs {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 4px;
            background: var(--surface);
            padding: 4px;
            border-radius: 4px;
            margin-bottom: 32px;
            border: 1px solid var(--border);
        }

        .tab {
            padding: 12px 8px;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 2px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            font-weight: 500;
            color: var(--muted);
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .tab:hover {
            color: var(--secondary);
            border-color: var(--border);
        }

        .tab.active {
            background: var(--primary);
            color: var(--bg);
            font-weight: 700;
            border-color: var(--primary);
            box-shadow: var(--glow);
        }

        .panel {
            display: none;
        }

        .panel.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .card {
            background: var(--surface);
            border-radius: 4px;
            padding: 24px;
            margin-bottom: 16px;
            border: 1px solid var(--border);
            position: relative;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }

        .card-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.875rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group:last-child {
            margin-bottom: 0;
        }

        label {
            display: block;
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--secondary);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        input[type="text"],
        input[type="url"],
        input[type="password"],
        select,
        textarea {
            width: 100%;
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: 2px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            color: var(--text);
            background: var(--bg);
            transition: all 0.2s ease;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 1px var(--primary), var(--glow);
        }

        input::placeholder, textarea::placeholder {
            color: var(--muted);
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        select {
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2300d4ff' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            padding-right: 36px;
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            font-size: 0.875rem;
            color: var(--text);
        }

        input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: var(--primary);
            cursor: pointer;
            border: 1px solid var(--border);
            border-radius: 2px;
        }

        small {
            display: block;
            margin-top: 6px;
            font-size: 0.7rem;
            color: var(--muted);
        }

        a {
            color: var(--secondary);
            text-decoration: none;
            transition: color 0.2s ease;
        }

        a:hover {
            color: var(--primary);
            text-decoration: underline;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 24px;
            border: 1px solid;
            border-radius: 2px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .btn-primary {
            background: var(--primary);
            color: var(--bg);
            border-color: var(--primary);
            width: 100%;
        }

        .btn-primary:hover {
            background: var(--primary-dim);
            box-shadow: var(--glow);
            transform: translateY(-1px);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-primary:disabled {
            background: var(--muted);
            border-color: var(--muted);
            color: var(--bg);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .btn-secondary {
            background: transparent;
            color: var(--secondary);
            border-color: var(--secondary);
        }

        .btn-secondary:hover {
            background: var(--secondary);
            color: var(--bg);
        }

        .btn-danger {
            background: transparent;
            color: var(--accent);
            border-color: var(--accent);
        }

        .btn-danger:hover {
            background: var(--accent);
            color: var(--bg);
        }

        .btn-sm {
            padding: 8px 12px;
            font-size: 0.7rem;
        }

        .progress-area {
            display: none;
            margin-top: 20px;
        }

        .progress-area.show {
            display: block;
        }

        .progress-bar {
            height: 4px;
            background: var(--bg);
            border-radius: 2px;
            overflow: hidden;
            margin-bottom: 12px;
            border: 1px solid var(--border);
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            width: 0%;
            transition: width 0.4s ease;
            box-shadow: var(--glow);
        }

        .status-msg {
            padding: 12px 14px;
            border-radius: 2px;
            font-size: 0.8rem;
            display: none;
            border: 1px solid;
        }

        .status-msg.show {
            display: block;
        }

        .status-msg a {
            color: inherit;
            font-weight: 500;
        }

        .status-success {
            background: rgba(0, 255, 159, 0.1);
            color: var(--primary);
            border-color: var(--primary);
        }

        .status-error {
            background: rgba(255, 0, 170, 0.1);
            color: var(--accent);
            border-color: var(--accent);
        }

        .status-info {
            background: rgba(0, 212, 255, 0.1);
            color: var(--secondary);
            border-color: var(--secondary);
        }

        .results-section {
            background: var(--surface);
            border-radius: 4px;
            overflow: hidden;
            display: none;
            border: 1px solid var(--border);
        }

        .results-section.show {
            display: block;
        }

        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            background: var(--surface-2);
        }

        .results-header h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .results-list {
            max-height: 320px;
            overflow-y: auto;
        }

        .result-item {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.15s ease;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .result-item:hover {
            background: var(--surface-2);
        }

        .result-info {
            flex: 1;
            min-width: 0;
        }

        .result-name {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text);
            margin-bottom: 4px;
        }

        .result-meta {
            font-size: 0.75rem;
            color: var(--muted);
        }

        .result-actions {
            display: flex;
            gap: 8px;
            flex-shrink: 0;
            margin-left: 16px;
        }

        .empty-state {
            text-align: center;
            padding: 48px 24px;
            color: var(--muted);
            font-size: 0.875rem;
        }

        .history-item {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border);
            transition: background 0.15s ease;
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .history-item:hover {
            background: var(--surface-2);
        }

        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }

        .history-type {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text);
        }

        .history-badge {
            padding: 4px 8px;
            border-radius: 2px;
            font-size: 0.65rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .badge-success {
            background: rgba(0, 255, 159, 0.15);
            color: var(--primary);
            border: 1px solid var(--primary);
        }

        .badge-error {
            background: rgba(255, 0, 170, 0.15);
            color: var(--accent);
            border: 1px solid var(--accent);
        }

        .badge-processing {
            background: rgba(0, 212, 255, 0.15);
            color: var(--secondary);
            border: 1px solid var(--secondary);
        }

        .history-input {
            font-size: 0.8rem;
            color: var(--muted);
            word-break: break-all;
            margin-bottom: 8px;
        }

        .history-meta {
            display: flex;
            gap: 16px;
            font-size: 0.7rem;
            color: var(--muted);
        }

        .config-grid {
            display: grid;
            gap: 16px;
        }

        @media (max-width: 640px) {
            .app {
                padding: 24px 16px 60px;
            }

            .header {
                margin-bottom: 32px;
            }

            .logo-text {
                font-size: 1.5rem;
            }

            .tabs {
                grid-template-columns: repeat(3, 1fr);
            }

            .tab {
                padding: 10px 8px;
                font-size: 0.65rem;
            }

            .card {
                padding: 16px;
            }

            .result-actions {
                flex-direction: column;
            }

            .result-actions .btn {
                width: 100%;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                transition-duration: 0.01ms !important;
                animation-duration: 0.01ms !important;
            }
        }
    </style>
</head>
<body>
    <div class="app">
        <header class="header">
            <div class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" x2="12" y1="19" y2="22"/>
                    </svg>
                </div>
                <span class="logo-text">Summary4U</span>
            </div>
            <p class="tagline">Audio/Video Summarization Engine</p>
        </header>

        <nav class="tabs">
            <button class="tab active" data-tab="url">URL处理</button>
            <button class="tab" data-tab="audio">本地文件</button>
            <button class="tab" data-tab="batch">批量处理</button>
            <button class="tab" data-tab="results">输出</button>
            <button class="tab" data-tab="history">日志</button>
            <button class="tab" data-tab="config">配置</button>
        </nav>

        <!-- URL Panel -->
        <div id="url" class="panel active">
            <div class="card">
                <h2 class="card-title">视频链接处理</h2>
                <form id="urlForm">
                    <div class="form-group">
                        <label for="videoUrl">视频URL</label>
                        <input type="url" id="videoUrl" placeholder="https://youtube.com/..." required>
                    </div>
                    <div class="form-group">
                        <label for="whisperModel">转录模型</label>
                        <select id="whisperModel">
                            <option value="tiny">Tiny</option>
                            <option value="base">Base</option>
                            <option value="small" selected>Small</option>
                            <option value="medium">Medium</option>
                            <option value="large">Large</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="promptTemplate">摘要模板</label>
                        <select id="promptTemplate">
                            <option value="default课堂笔记">课堂笔记</option>
                            <option value="课堂内容">课堂内容</option>
                            <option value="双语总结">双语总结</option>
                            <option value="会议纪要">会议纪要</option>
                            <option value="业务复盘">业务复盘</option>
                            <option value="精炼摘要">精炼摘要</option>
                            <option value="专业课程">专业课程</option>
                            <option value="短视频素材">短视频素材</option>
                            <option value="综合总结">综合总结</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="customPrompt">自定义提示词</label>
                        <textarea id="customPrompt" placeholder="可选，覆盖模板设置"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="withScreenshots">
                            生成截图
                        </label>
                    </div>
                    <button type="submit" class="btn btn-primary">开始处理</button>
                </form>
                <div id="urlProgress" class="progress-area">
                    <div class="progress-bar"><div id="urlProgressFill" class="progress-fill"></div></div>
                    <div id="urlStatusMsg" class="status-msg"></div>
                </div>
            </div>
        </div>

        <!-- Audio Panel -->
        <div id="audio" class="panel">
            <div class="card">
                <h2 class="card-title">本地文件处理</h2>
                <form id="audioForm">
                    <div class="form-group">
                        <label for="audioFile">选择文件</label>
                        <input type="file" id="audioFile" accept=".mp3,.wav,.m4a,.mp4,.aac,.flac,.wma,.amr" required>
                        <small>MP3, WAV, M4A, AAC, FLAC</small>
                    </div>
                    <div class="form-group">
                        <label for="audioWhisperModel">转录模型</label>
                        <select id="audioWhisperModel">
                            <option value="tiny">Tiny</option>
                            <option value="base">Base</option>
                            <option value="small" selected>Small</option>
                            <option value="medium">Medium</option>
                            <option value="large">Large</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="audioLanguage">音频语言</label>
                        <select id="audioLanguage">
                            <option value="">自动检测</option>
                            <option value="zh">中文</option>
                            <option value="en">英语</option>
                            <option value="ja">日语</option>
                            <option value="ko">韩语</option>
                            <option value="fr">法语</option>
                            <option value="de">德语</option>
                            <option value="es">西班牙语</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="audioPromptTemplate">摘要模板</label>
                        <select id="audioPromptTemplate">
                            <option value="default课堂笔记">课堂笔记</option>
                            <option value="课堂内容">课堂内容</option>
                            <option value="双语总结">双语总结</option>
                            <option value="会议纪要">会议纪要</option>
                            <option value="业务复盘">业务复盘</option>
                            <option value="精炼摘要">精炼摘要</option>
                            <option value="专业课程">专业课程</option>
                            <option value="短视频素材">短视频素材</option>
                            <option value="综合总结">综合总结</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="audioCustomPrompt">自定义提示词</label>
                        <textarea id="audioCustomPrompt" placeholder="可选，覆盖模板设置"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">上传处理</button>
                </form>
                <div id="audioProgress" class="progress-area">
                    <div class="progress-bar"><div id="audioProgressFill" class="progress-fill"></div></div>
                    <div id="audioStatusMsg" class="status-msg"></div>
                </div>
            </div>
        </div>

        <!-- Batch Panel -->
        <div id="batch" class="panel">
            <div class="card">
                <h2 class="card-title">批量处理</h2>
                <div class="form-group">
                    <label for="batchUploadDir">文件夹路径</label>
                    <input type="text" id="batchUploadDir" value="uploads" placeholder="uploads">
                </div>
                <div class="form-group">
                    <label for="batchWhisperModel">转录模型</label>
                    <select id="batchWhisperModel">
                        <option value="tiny">Tiny</option>
                        <option value="base">Base</option>
                        <option value="small" selected>Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="batchPromptTemplate">摘要模板</label>
                    <select id="batchPromptTemplate">
                        <option value="default课堂笔记">课堂笔记</option>
                        <option value="课堂内容">课堂内容</option>
                        <option value="双语总结">双语总结</option>
                        <option value="会议纪要">会议纪要</option>
                        <option value="业务复盘">业务复盘</option>
                        <option value="精炼摘要">精炼摘要</option>
                        <option value="专业课程">专业课程</option>
                        <option value="短视频素材">短视频素材</option>
                        <option value="综合总结">综合总结</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="batchCustomPrompt">自定义提示词</label>
                    <textarea id="batchCustomPrompt" placeholder="可选，覆盖模板设置"></textarea>
                </div>
                <button type="button" onclick="startBatchProcess()" class="btn btn-primary">开始批量</button>
                <div id="batchProgress" class="progress-area">
                    <div class="progress-bar"><div id="batchProgressFill" class="progress-fill"></div></div>
                    <div id="batchStatusMsg" class="status-msg"></div>
                </div>
            </div>
        </div>

        <!-- Results Panel -->
        <div id="results" class="panel">
            <div class="results-section" id="resultsSection">
                <div class="results-header">
                    <h3>生成文件</h3>
                    <button onclick="loadResults()" class="btn btn-secondary btn-sm">刷新</button>
                </div>
                <div class="results-list" id="resultsList"></div>
            </div>
            <div class="empty-state" id="noResultsMsg">暂无处理结果</div>
        </div>

        <!-- History Panel -->
        <div id="history" class="panel">
            <div class="results-section" id="historySection">
                <div class="results-header">
                    <h3>处理日志</h3>
                    <div style="display:flex;gap:8px;">
                        <button onclick="loadTaskHistory()" class="btn btn-secondary btn-sm">刷新</button>
                        <button onclick="clearTaskHistory()" class="btn btn-danger btn-sm">清空</button>
                    </div>
                </div>
                <div class="results-list" id="historyList"></div>
            </div>
            <div class="empty-state" id="noHistoryMsg">暂无历史记录</div>
        </div>

        <!-- Config Panel -->
        <div id="config" class="panel">
            <div class="card">
                <h2 class="card-title">API配置</h2>
                <div class="config-grid">
                    <div class="form-group">
                        <label for="apiKeyTikhub">TikHub API</label>
                        <input type="password" id="apiKeyTikhub" placeholder="抖音/TikTok下载">
                        <small><a href="https://user.tikhub.io/users/signin" target="_blank">tikhub.io</a></small>
                    </div>
                    <div class="form-group">
                        <label for="apiKeyDeepseek">DeepSeek API</label>
                        <input type="password" id="apiKeyDeepseek" placeholder="AI摘要">
                    </div>
                    <div class="form-group">
                        <label for="apiKeyOpenai">OpenAI API</label>
                        <input type="password" id="apiKeyOpenai" placeholder="可选">
                    </div>
                    <div class="form-group">
                        <label for="apiKeyAnthropic">Anthropic API</label>
                        <input type="password" id="apiKeyAnthropic" placeholder="可选">
                    </div>
                </div>
                <button onclick="saveApiConfig()" class="btn btn-primary" style="margin-top:20px;">保存</button>
                <div id="apiConfigMsg" class="status-msg" style="margin-top:16px;"></div>
            </div>
        </div>
    </div>

    <script>
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
                if (tab.dataset.tab === 'results') loadResults();
                if (tab.dataset.tab === 'history') loadTaskHistory();
                if (tab.dataset.tab === 'config') loadApiConfig();
            });
        });

        document.getElementById('urlForm').addEventListener('submit', async e => {
            e.preventDefault();
            const url = document.getElementById('videoUrl').value.trim();
            const model = document.getElementById('whisperModel').value;
            const template = document.getElementById('promptTemplate').value;
            const custom = document.getElementById('customPrompt').value.trim();
            const withScreenshots = document.getElementById('withScreenshots').checked;
            if (!url) {
                showProgress('url', '请输入视频URL', 'error');
                return;
            }

            showProgress('url', '正在发送请求...', 'info');
            try {
                const res = await fetch('/process-url', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, model, prompt_template: template, prompt: custom || null, with_screenshots: withScreenshots })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || '请求失败');
                await pollTaskStatus(data.task_id, 'url');
            } catch (err) {
                showProgress('url', '错误: ' + err.message, 'error');
            }
        });

        document.getElementById('audioForm').addEventListener('submit', async e => {
            e.preventDefault();
            const file = document.getElementById('audioFile').files[0];
            const model = document.getElementById('audioWhisperModel').value;
            const lang = document.getElementById('audioLanguage').value;
            const template = document.getElementById('audioPromptTemplate').value;
            const custom = document.getElementById('audioCustomPrompt').value.trim();
            if (!file) {
                showProgress('audio', '请选择音频文件', 'error');
                return;
            }

            const fd = new FormData();
            fd.append('file', file);
            fd.append('model', model);
            if (lang) fd.append('language', lang);
            fd.append('prompt_template', template);
            if (custom) fd.append('prompt', custom);

            showProgress('audio', '正在上传文件...', 'info');
            try {
                const res = await fetch('/upload-audio', { method: 'POST', body: fd });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || '上传失败');
                await pollTaskStatus(data.task_id, 'audio');
            } catch (err) {
                showProgress('audio', '错误: ' + err.message, 'error');
            }
        });

        async function startBatchProcess() {
            const dir = document.getElementById('batchUploadDir').value.trim() || 'uploads';
            const model = document.getElementById('batchWhisperModel').value;
            const template = document.getElementById('batchPromptTemplate').value;
            const custom = document.getElementById('batchCustomPrompt').value.trim();

            showProgress('batch', '正在开始批量处理...', 'info');
            try {
                const res = await fetch('/batch-process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ upload_dir: dir, model, prompt_template: template, prompt: custom || null })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || '批量处理请求失败');
                await pollTaskStatus(data.task_id, 'batch');
            } catch (err) {
                showProgress('batch', '错误: ' + err.message, 'error');
            }
        }

        async function pollTaskStatus(taskId, prefix) {
            let status;
            do {
                await new Promise(r => setTimeout(r, 2000));
                try {
                    const res = await fetch(`/task-status/${taskId}`);
                    status = await res.json();
                } catch (err) {
                    showProgress(prefix, '无法获取任务状态', 'error');
                    return;
                }
                const fill = document.getElementById(prefix + 'ProgressFill');
                const msg = document.getElementById(prefix + 'StatusMsg');
                if (fill) fill.style.width = status.progress + '%';
                if (msg) {
                    if (status.status === 'completed') {
                        msg.className = 'status-msg status-success show';
                        msg.innerHTML = status.message + (status.result_path ? '<br><a href="/download-result/' + encodeURIComponent(status.result_path) + '" target="_blank">点击下载结果</a>' : '');
                    } else if (status.status === 'error') {
                        msg.className = 'status-msg status-error show';
                        msg.textContent = status.message;
                    } else {
                        msg.className = 'status-msg status-info show';
                        msg.textContent = status.message;
                    }
                }
            } while (status.status === 'processing');
        }

        function showProgress(prefix, msg, type) {
            document.getElementById(prefix + 'Progress').classList.add('show');
            document.getElementById(prefix + 'ProgressFill').style.width = '5%';
            const el = document.getElementById(prefix + 'StatusMsg');
            el.className = 'status-msg status-' + type + ' show';
            el.textContent = msg;
        }

        async function loadResults() {
            try {
                const res = await fetch('/api/results');
                const data = await res.json();
                const list = document.getElementById('resultsList');
                const section = document.getElementById('resultsSection');
                const empty = document.getElementById('noResultsMsg');

                if (data.results && data.results.length > 0) {
                    list.innerHTML = data.results.map(r => `
                        <div class="result-item">
                            <div class="result-info">
                                <div class="result-name">${r.filename}</div>
                                <div class="result-meta">${r.modified} · ${(r.size / 1024 / 1024).toFixed(2)} MB</div>
                            </div>
                            <div class="result-actions">
                                <a href="/download-result/${encodeURIComponent(r.path)}" target="_blank"><button class="btn btn-secondary btn-sm">下载</button></a>
                            </div>
                        </div>
                    `).join('');
                    section.classList.add('show');
                    empty.style.display = 'none';
                } else {
                    section.classList.remove('show');
                    empty.style.display = 'block';
                }
            } catch (err) { console.error(err); }
        }

        async function loadTaskHistory() {
            try {
                const res = await fetch('/api/task-history');
                const data = await res.json();
                const list = document.getElementById('historyList');
                const section = document.getElementById('historySection');
                const empty = document.getElementById('noHistoryMsg');

                if (data.history && data.history.length > 0) {
                    const typeMap = { video_url: '视频链接', local_audio: '本地音频', batch_process: '批量处理' };
                    const statusMap = { completed: ['已完成', 'badge-success'], error: ['失败', 'badge-error'], processing: ['处理中', 'badge-processing'] };
                    list.innerHTML = data.history.map(t => {
                        const [tText, tClass] = (statusMap[t.status] || ['未知', 'badge-processing']);
                        const input = t.input.length > 60 ? t.input.substring(0, 60) + '...' : t.input;
                        const start = new Date(t.start_time).toLocaleString('zh-CN');
                        return `
                            <div class="history-item">
                                <div class="history-header">
                                    <span class="history-type">${typeMap[t.type] || t.type}</span>
                                    <span class="history-badge ${tClass[1]}">${tClass[0]}</span>
                                </div>
                                <div class="history-input">${input}</div>
                                <div class="history-meta">
                                    <span>模型: ${t.model}</span>
                                    <span>${start}</span>
                                </div>
                            </div>
                        `;
                    }).join('');
                    section.classList.add('show');
                    empty.style.display = 'none';
                } else {
                    section.classList.remove('show');
                    empty.style.display = 'block';
                }
            } catch (err) { console.error(err); }
        }

        async function clearTaskHistory() {
            if (!confirm('确定要清空所有历史记录吗？')) return;
            await fetch('/api/task-history', { method: 'DELETE' });
            loadTaskHistory();
        }

        async function loadApiConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                document.getElementById('apiKeyTikhub').value = data.api_keys.tikhub || '';
                document.getElementById('apiKeyDeepseek').value = data.api_keys.deepseek || '';
                document.getElementById('apiKeyOpenai').value = data.api_keys.openai || '';
                document.getElementById('apiKeyAnthropic').value = data.api_keys.anthropic || '';
            } catch (err) { console.error(err); }
        }

        async function saveApiConfig() {
            const keys = {
                tikhub: document.getElementById('apiKeyTikhub').value.trim(),
                deepseek: document.getElementById('apiKeyDeepseek').value.trim(),
                openai: document.getElementById('apiKeyOpenai').value.trim(),
                anthropic: document.getElementById('apiKeyAnthropic').value.trim()
            };
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_keys: keys })
                });
                const el = document.getElementById('apiConfigMsg');
                if (res.ok) {
                    el.className = 'status-msg status-success show';
                    el.textContent = '配置已保存';
                    loadApiConfig();
                } else {
                    el.className = 'status-msg status-error show';
                    el.textContent = '保存失败';
                }
                setTimeout(() => el.classList.remove('show'), 4000);
            } catch (err) {
                const el = document.getElementById('apiConfigMsg');
                el.className = 'status-msg status-error show';
                el.textContent = '保存失败: ' + err.message;
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)



@app.post("/process-url")
async def process_video_url_endpoint(
    url: str = Form(None),
    model: str = Form(default="small"),
    prompt_template: str = Form(default="default课堂笔记"),
    prompt: Optional[str] = Form(default=None),
    with_screenshots: bool = Form(default=False),
    # 为支持JSON请求添加参数
    request: Request = None
):
    # 检查请求是否为JSON格式
    if request and request.headers.get("content-type") == "application/json":
        try:
            body = await request.json()
            url = body.get("url", url)
            model = body.get("model", model)
            prompt_template = body.get("prompt_template", prompt_template)
            prompt = body.get("prompt", prompt)
            with_screenshots = body.get("with_screenshots", with_screenshots)
        except:
            pass  # 如果JSON解析失败，使用表单参数


    # 验证模型名称，确保是有效的 whisper 模型
    valid_models = ["tiny", "tiny.en", "base", "base.en", "small", "small.en",
                    "medium", "medium.en", "large", "large-v1", "large-v2",
                    "large-v3", "large-v3-turbo", "turbo"]
    if model not in valid_models:
        print(f"[WARNING] 无效的模型名称：{model}，使用默认模型 small")
        model = "small"
    # 确保URL不为空
    if not url:
        raise HTTPException(status_code=422, detail="URL是必需的")
    task_id = str(uuid.uuid4())

    # 确定使用哪个提示词
    # 安全的模板处理（避免 KeyError）
    if prompt_template not in prompt_templates:
        print(f"[WARNING] 未知的模板：{prompt_template}，使用默认模板")
        prompt_template = "default 课堂笔记"
    prompt_to_use = prompt if prompt else prompt_templates[prompt_template]

    # 生成输出文件路径
    auto_filename = generate_filename(url, has_summary=True, is_local=False)
    output_path = os.path.join("summaries", auto_filename)

    # 初始化任务状态
    task_status[task_id] = {"status": "processing", "progress": 0, "message": "初始化..."}

    # 在后台线程中运行处理任务
    thread = threading.Thread(
        target=process_video_url_task,
        args=(task_id, url, model, prompt_to_use, output_path, with_screenshots)
    )
    thread.start()

    return {"task_id": task_id}


@app.post("/upload-audio")
async def upload_audio_endpoint(
    file: UploadFile = File(...),
    model: str = Form(default="small"),
    language: Optional[str] = Form(default=None),
    prompt_template: str = Form(default="default课堂笔记"),
    prompt: Optional[str] = Form(default=None)
):
    task_id = str(uuid.uuid4())
    
    # 确定使用哪个提示词
    # 安全的模板处理（避免 KeyError）
    if prompt_template not in prompt_templates:
        print(f"[WARNING] 未知的模板：{prompt_template}，使用默认模板")
        prompt_template = "default 课堂笔记"
    prompt_to_use = prompt if prompt else prompt_templates[prompt_template]
    
    # 保存上传的文件
    file_location = os.path.join("downloads", file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 生成输出文件路径
    auto_filename = generate_filename(file_location, has_summary=True, is_local=True)
    output_path = os.path.join("summaries", auto_filename)
    
    # 初始化任务状态
    task_status[task_id] = {"status": "processing", "progress": 0, "message": "初始化..."}
    
    # 在后台线程中运行处理任务
    thread = threading.Thread(
        target=process_local_audio_task,
        args=(task_id, file_location, model, prompt_to_use, output_path, language)
    )
    thread.start()
    
    return {"task_id": task_id}


@app.post("/batch-process")
async def batch_process_endpoint(
    upload_dir: str = Form(None),
    model: str = Form(default="small"),
    prompt_template: str = Form(default="default课堂笔记"),
    prompt: Optional[str] = Form(default=None),
    # 为支持JSON请求添加参数
    request: Request = None
):
    # 检查请求是否为JSON格式
    if request and request.headers.get("content-type") == "application/json":
        try:
            body = await request.json()
            upload_dir = body.get("upload_dir", upload_dir) or "uploads"
            model = body.get("model", model)
            prompt_template = body.get("prompt_template", prompt_template)
            prompt = body.get("prompt", prompt)
        except:
            pass  # 如果JSON解析失败，使用表单参数

    # 确保upload_dir不为空
    if not upload_dir:
        upload_dir = "uploads"
    task_id = str(uuid.uuid4())
    
    # 确定使用哪个提示词
    # 安全的模板处理（避免 KeyError）
    if prompt_template not in prompt_templates:
        print(f"[WARNING] 未知的模板：{prompt_template}，使用默认模板")
        prompt_template = "default 课堂笔记"
    prompt_to_use = prompt if prompt else prompt_templates[prompt_template]
    
    # 初始化任务状态
    task_status[task_id] = {"status": "processing", "progress": 0, "message": "初始化批量处理..."}
    
    # 记录任务开始时间
    start_time = datetime.now()

    # 添加任务到历史记录
    task_info = {
        "task_id": task_id,
        "type": "batch_process",
        "input": upload_dir,
        "model": model,
        "prompt_template_used": prompt_template,
        "language": None,
        "start_time": start_time,
        "end_time": None,
        "status": "processing",
        "result_path": None
    }
    task_history.append(task_info)

    def run_batch_process():
        try:
            task_status[task_id] = {"status": "processing", "progress": 5, "message": "正在验证上传目录..."}

            # 验证上传目录
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                task_status[task_id] = {"status": "processing", "progress": 10, "message": f"创建上传目录: {upload_dir}"}

            task_status[task_id] = {"status": "processing", "progress": 20, "message": "开始批量处理..."}
            print(f"[{task_id}] 开始批量处理目录: {upload_dir}")

            process_batch(
                upload_dir=upload_dir,
                model=model,
                prompt_to_use=prompt_to_use,
                prompt_template=prompt_template
            )
            # 更新任务历史记录
            task_info["end_time"] = datetime.now()
            task_info["status"] = "completed"

            task_status[task_id] = {"status": "completed", "progress": 100, "message": "批量处理完成！"}
            print(f"[{task_id}] 批量处理完成")
        except Exception as e:
            # 更新任务历史记录
            task_info["end_time"] = datetime.now()
            task_info["status"] = "error"
            task_info["error"] = str(e)

            task_status[task_id] = {"status": "error", "progress": 0, "message": f"批量处理失败: {str(e)}", "error": str(e)}
            print(f"[{task_id}] 批量处理失败: {str(e)}")
    
    # 在后台线程中运行批量处理
    thread = threading.Thread(target=run_batch_process)
    thread.start()
    
    return {"task_id": task_id}


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_status[task_id]


@app.get("/download-result/{file_path:path}")
async def download_result(file_path: str):
    import urllib.parse
    import zipfile
    import tempfile

    # 解码文件路径
    decoded_path = urllib.parse.unquote(file_path)

    if not os.path.exists(decoded_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 如果是目录，打包成 zip 文件
    if os.path.isdir(decoded_path):
        zip_filename = os.path.basename(decoded_path) + '.zip'
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()

        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(decoded_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(decoded_path))
                    zipf.write(file_path, arcname)

        from fastapi.responses import FileResponse
        return FileResponse(
            path=temp_zip.name,
            media_type='application/zip',
            filename=zip_filename
        )
    else:
        from fastapi.responses import FileResponse
        return FileResponse(
            path=decoded_path,
            media_type='text/markdown',
            filename=os.path.basename(decoded_path)
        )


@app.get("/api/prompt-templates")
async def get_prompt_templates():
    """获取所有可用的提示词模板"""
    return {"templates": [
        {"name": "短视频知识", "description": "短视频知识内容总结框架，适合 1-15 分钟知识类短视频"},
        {"name": "课堂内容", "description": "课堂类内容总结，适合在线课程、培训讲座、系统教学"},
        {"name": "双语总结", "description": "双语总结内容，适合英文视频、外语学习材料"},
        {"name": "会议纪要", "description": "会议纪要和核心要点提炼，适合会议录音、讨论记录"},
        {"name": "业务复盘", "description": "业务复盘录音内容提炼 SOP 和错误总结"},
        {"name": "精炼摘要", "description": "提取核心要点和精华"},
        {"name": "专业课程", "description": "学术笔记，适合专业课程、理论推导"},
        {"name": "短视频素材", "description": "短视频创作素材包"},
        {"name": "综合总结", "description": "综合性视频总结模板"}
    ]}



@app.get("/api/models")
async def get_models():
    """获取所有可用的Whisper模型"""
    return {"models": [
        {"name": "tiny", "description": "最快但准确性最低 (约32x实时速度)"},
        {"name": "base", "description": "快速且准确 (约16x实时速度)"},
        {"name": "small", "description": "平衡速度和准确性 (约6x实时速度) - 默认值"},
        {"name": "medium", "description": "较慢但更准确 (约2x实时速度)"},
        {"name": "large", "description": "最准确但最慢 (接近实时速度)"},
        {"name": "large-v1", "description": "大模型版本1"},
        {"name": "large-v2", "description": "大模型版本2"},
        {"name": "large-v3", "description": "大模型版本3"}
    ]}


@app.get("/api/results")
async def get_results():
    """获取所有生成的总结结果"""
    import glob
    summary_files = glob.glob("summaries/*.md")
    results = []
    for file_path in summary_files:
        try:
            # 获取文件修改时间
            mod_time = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')

            # 获取文件大小
            size = os.path.getsize(file_path)

            results.append({
                "filename": os.path.basename(file_path),
                "path": file_path,
                "size": size,
                "modified": mod_date
            })
        except Exception:
            # 如果无法获取文件信息，跳过该文件
            continue

    return {"results": results}


@app.get("/api/task-history")
async def get_task_history():
    """获取任务历史记录"""
    history = []
    for task in task_history:
        task_copy = task.copy()
        # 转换时间为字符串格式
        if isinstance(task_copy["start_time"], datetime):
            task_copy["start_time"] = task_copy["start_time"].strftime('%Y-%m-%d %H:%M:%S')
        if task_copy["end_time"] and isinstance(task_copy["end_time"], datetime):
            task_copy["end_time"] = task_copy["end_time"].strftime('%Y-%m-%d %H:%M:%S')
        history.append(task_copy)

    # 按开始时间倒序排列
    history.sort(key=lambda x: x["start_time"], reverse=True)

    return {"history": history}


@app.delete("/api/task-history")
async def clear_task_history():
    """清空任务历史记录"""
    global task_history
    task_history = []
    return {"message": "任务历史记录已清空"}


@app.get("/api/config")
async def get_api_config():
    """获取当前API密钥配置（已脱敏）"""
    config = config_manager.config
    api_keys = config.get("api_keys", {})
    masked = {}
    for provider in ["tikhub", "deepseek", "openai", "anthropic"]:
        key = api_keys.get(provider, "")
        masked[provider] = key[-4:].rjust(len(key), "*") if key else ""
    return {"api_keys": masked}


@app.post("/api/config")
async def save_api_config(data: dict):
    """保存API密钥配置"""
    api_keys = data.get("api_keys", {})
    for provider in ["tikhub", "deepseek", "openai", "anthropic"]:
        key = api_keys.get(provider, "")
        if key:
            config_manager.set_api_key(provider, key)
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)