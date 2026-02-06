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
import uvicorn

# 添加src目录到Python路径
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_dir)

# 使用绝对导入
from src.audio import download_audio
from src.transcribe import transcribe_audio, transcribe_local_audio
from src.summarize import summarize_text
from src.prompts import prompt_templates
from src.audio_handler import handle_audio_upload
from src.utils import safe_filename
from src.batch_processor import process_batch
from src.config import config_manager, get_api_key, set_api_key

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


def process_video_url_task(task_id: str, video_url: str, model: str, prompt_to_use: str, output_path: str):
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
        "start_time": start_time,
        "end_time": None,
        "status": "processing",
        "result_path": None
    }
    task_history.append(task_info)

    try:
        task_status[task_id] = {"status": "processing", "progress": 5, "message": "正在验证视频URL..."}

        print(f"[{task_id}] 验证视频URL: {video_url}")
        if not video_url or not (video_url.startswith('http://') or video_url.startswith('https://')):
            raise ValueError("无效的视频URL")

        task_status[task_id] = {"status": "processing", "progress": 10, "message": "下载并提取音频..."}

        print(f"[{task_id}] 下载并提取音频...")
        audio_path = download_audio(video_url)
        print(f"[{task_id}] 音频已保存: {audio_path}")
        task_status[task_id] = {"status": "processing", "progress": 20, "message": "开始转录..."}

        print(f"[{task_id}] 转录音频 (使用模型: {model})...")
        print(f"[{task_id}] 提示：转录过程可能需要几分钟时间，请耐心等待...")
        transcript = transcribe_audio(audio_path, model=model)
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


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>音频/视频总结工具 Web UI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            /* Base UI inspired color palette */
            --gray-50: #f8fafc;
            --gray-100: #f1f5f9;
            --gray-200: #e2e8f0;
            --gray-300: #cbd5e1;
            --gray-400: #94a3b8;
            --gray-500: #64748b;
            --gray-600: #475569;
            --gray-700: #334155;
            --gray-800: #1e293b;
            --gray-900: #0f172a;
            
            /* Primary colors */
            --primary-50: #eff6ff;
            --primary-100: #dbeafe;
            --primary-200: #bfdbfe;
            --primary-300: #93c5fd;
            --primary-400: #60a5fa;
            --primary-500: #3b82f6;
            --primary-600: #2563eb;
            --primary-700: #1d4ed8;
            --primary-800: #1e40af;
            --primary-900: #1e3a8a;
            
            /* Success, Warning, Error colors */
            --success-50: #f0fdf4;
            --success-100: #dcfce7;
            --success-200: #bbf7d0;
            --success-300: #86efac;
            --success-400: #4ade80;
            --success-500: #22c55e;
            --success-600: #16a34a;
            --success-700: #15803d;
            --success-800: #166534;
            --success-900: #14532d;
            
            --warning-50: #fffbeb;
            --warning-100: #fef3c7;
            --warning-200: #fde68a;
            --warning-300: #fcd34d;
            --warning-400: #fbbf24;
            --warning-500: #f59e0b;
            --warning-600: #d97706;
            --warning-700: #b45309;
            --warning-800: #92400e;
            --warning-900: #78350f;
            
            --error-50: #fef2f2;
            --error-100: #fee2e2;
            --error-200: #fecaca;
            --error-300: #fca5a5;
            --error-400: #f87171;
            --error-500: #ef4444;
            --error-600: #dc2626;
            --error-700: #b91c1c;
            --error-800: #991b1b;
            --error-900: #7f1d1d;
            
            /* Modern UI variables */
            --bg-body: var(--gray-50);
            --bg-card: white;
            --bg-panel: var(--gray-100);
            --text-primary: var(--gray-900);
            --text-secondary: var(--gray-600);
            --text-muted: var(--gray-500);
            --border: var(--gray-200);
            --primary: var(--primary-600);
            --primary-hover: var(--primary-700);
            --success: var(--success-600);
            --warning: var(--warning-600);
            --error: var(--error-600);
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            --radius-sm: 0.375rem;
            --radius: 0.5rem;
            --radius-md: 0.625rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
            --transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
        }

        body {
            background-color: var(--bg-body);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            padding: 1rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-card);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            display: grid;
            grid-template-rows: auto 1fr;
        }

        header {
            background: linear-gradient(135deg, var(--primary), #4f46e5);
            color: white;
            padding: 2rem 2.5rem;
            text-align: center;
        }

        .header-content {
            max-width: 800px;
            margin: 0 auto;
        }

        h1 {
            font-size: 2.25rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
        }

        .header-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }

        .tabs-container {
            display: flex;
            background-color: var(--bg-panel);
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
        }

        .tab-button {
            flex: 1;
            min-width: 120px;
            padding: 1rem 1.5rem;
            background: transparent;
            color: var(--text-secondary);
            border: none;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            transition: var(--transition);
            position: relative;
            white-space: nowrap;
        }

        .tab-button:hover {
            color: var(--text-primary);
            background-color: rgba(255, 255, 255, 0.5);
        }

        .tab-button.active {
            color: var(--primary);
            background-color: white;
        }

        .tab-button.active::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background-color: var(--primary);
        }

        .tab-content {
            display: none;
            padding: 2rem;
        }

        .tab-content.active {
            display: block;
            animation: fadeInSlideUp 0.3s ease-out;
        }

        @keyframes fadeInSlideUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .form-grid {
            display: grid;
            gap: 1.5rem;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        label {
            font-weight: 500;
            color: var(--text-primary);
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .tooltip-trigger {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.25rem;
            height: 1.25rem;
            border-radius: 50%;
            background-color: var(--gray-200);
            color: var(--gray-600);
            font-size: 0.75rem;
            cursor: help;
        }

        .tooltip {
            position: relative;
            display: inline-block;
        }

        .tooltip .tooltip-text {
            visibility: hidden;
            width: 280px;
            background-color: var(--gray-800);
            color: white;
            text-align: center;
            border-radius: var(--radius);
            padding: 0.75rem;
            position: absolute;
            z-index: 100;
            bottom: 125%;
            left: 50%;
            transform: translateX(-50%);
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.85rem;
            line-height: 1.4;
            box-shadow: var(--shadow-lg);
        }

        .tooltip:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        input, select, textarea {
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            font-size: 1rem;
            transition: var(--transition);
            background-color: white;
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }

        input[type="file"] {
            border: 2px dashed var(--border);
            padding: 1.5rem;
            text-align: center;
            background-color: var(--gray-50);
        }

        input[type="file"]:focus {
            border-color: var(--primary);
        }

        .input-hint {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }

        .btn {
            background-color: var(--primary);
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn:hover:not(:disabled) {
            background-color: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .btn:disabled {
            background-color: var(--gray-300);
            cursor: not-allowed;
            transform: none;
        }

        .btn-success {
            background-color: var(--success);
        }

        .btn-success:hover:not(:disabled) {
            background-color: var(--success-700);
        }

        .btn-warning {
            background-color: var(--warning);
        }

        .btn-warning:hover:not(:disabled) {
            background-color: var(--warning-700);
        }

        .btn-error {
            background-color: var(--error);
        }

        .btn-error:hover:not(:disabled) {
            background-color: var(--error-700);
        }

        .progress-container {
            margin-top: 1.5rem;
            display: none;
        }

        .progress-bar {
            width: 100%;
            height: 0.75rem;
            background-color: var(--gray-200);
            border-radius: 9999px;
            overflow: hidden;
            margin-bottom: 0.75rem;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), #6366f1);
            width: 0%;
            transition: width 0.4s ease;
            border-radius: 9999px;
        }

        .status-message {
            padding: 1rem;
            border-radius: var(--radius);
            display: none;
            font-size: 0.95rem;
            line-height: 1.5;
            margin-top: 1rem;
        }

        .status-message a {
            color: white;
            text-decoration: underline;
            margin-top: 0.5rem;
            display: inline-block;
        }

        .status-success {
            background-color: var(--success-50);
            color: var(--success-800);
            border: 1px solid var(--success-200);
        }

        .status-error {
            background-color: var(--error-50);
            color: var(--error-800);
            border: 1px solid var(--error-200);
        }

        .status-info {
            background-color: var(--primary-50);
            color: var(--primary-800);
            border: 1px solid var(--primary-200);
        }

        .results-container {
            margin-top: 1.5rem;
            border-radius: var(--radius);
            background-color: var(--bg-panel);
            display: none;
            border: 1px solid var(--border);
        }

        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
        }

        .results-header h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .results-list {
            max-height: 400px;
            overflow-y: auto;
            padding: 1rem;
        }

        .result-item {
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            background: white;
            border-radius: var(--radius);
            margin-bottom: 0.75rem;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
        }

        .result-item:hover {
            box-shadow: var(--shadow);
            transform: translateY(-2px);
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .result-info {
            flex: 1;
        }

        .result-title {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.25rem;
        }

        .result-meta {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .result-actions {
            display: flex;
            gap: 0.5rem;
            flex-shrink: 0;
            margin-left: 1rem;
        }

        .result-actions .btn {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }

        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-muted);
            font-size: 1rem;
        }

        .empty-state i {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: var(--gray-300);
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
            gap: 0.25rem;
        }

        .status-badge.completed {
            background-color: var(--success-100);
            color: var(--success-800);
        }

        .status-badge.error {
            background-color: var(--error-100);
            color: var(--error-800);
        }

        .status-badge.processing {
            background-color: var(--primary-100);
            color: var(--primary-800);
        }

        .task-details {
            margin-top: 0.5rem;
        }

        .task-input {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
            word-break: break-all;
        }

        .task-meta {
            display: flex;
            gap: 1.5rem;
            margin-top: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .action-buttons {
            display: flex;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }

        @media (max-width: 768px) {
            body {
                padding: 0.5rem;
            }

            .container {
                border-radius: var(--radius);
            }

            header {
                padding: 1.5rem;
            }

            h1 {
                font-size: 1.75rem;
            }

            .header-subtitle {
                font-size: 0.95rem;
            }

            .tab-content {
                padding: 1.5rem 1rem;
            }

            .tabs-container {
                flex-wrap: wrap;
            }

            .tab-button {
                padding: 0.75rem 1rem;
                font-size: 0.9rem;
            }

            .form-grid {
                gap: 1.25rem;
            }

            .result-actions {
                flex-direction: column;
            }

            .result-actions .btn {
                width: 100%;
            }

            .action-buttons {
                flex-direction: column;
            }

            .results-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.75rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <h1><i class="fas fa-microphone-alt"></i> 音频/视频总结工具</h1>
                <p class="header-subtitle">支持视频URL处理、本地音频上传和批量处理，提供实时进度监控和结果下载</p>
            </div>
        </header>

        <div class="tabs-container">
            <button class="tab-button active" data-tab="url"><i class="fas fa-link"></i> 视频URL处理</button>
            <button class="tab-button" data-tab="audio"><i class="fas fa-file-audio"></i> 本地音频处理</button>
            <button class="tab-button" data-tab="batch"><i class="fas fa-layer-group"></i> 批量处理</button>
            <button class="tab-button" data-tab="api_config"><i class="fas fa-cog"></i> API配置</button>
            <button class="tab-button" data-tab="results"><i class="fas fa-file-alt"></i> 查看结果</button>
            <button class="tab-button" data-tab="history"><i class="fas fa-history"></i> 任务历史</button>
        </div>

        <!-- 视频URL处理标签页 -->
        <div id="url" class="tab-content active">
            <h2 class="section-title"><i class="fas fa-link"></i> 处理视频URL</h2>
            <form id="urlForm" class="form-grid">
                <div class="form-group">
                    <label for="videoUrl">视频URL <span class="tooltip"><span class="tooltip-trigger"><i class="fas fa-question"></i></span><span class="tooltip-text">支持YouTube、Bilibili等平台的视频链接</span></span></label>
                    <input type="url" id="videoUrl" name="videoUrl" placeholder="https://www.youtube.com/watch?v=..." required>
                    <small class="input-hint">请输入有效的视频链接</small>
                </div>

                <div class="form-group">
                    <label for="whisperModel">Whisper模型大小 <span class="tooltip"><span class="tooltip-trigger"><i class="fas fa-question"></i></span><span class="tooltip-text">tiny: 最快但准确性最低 | small: 平衡速度和准确性 | large: 最准确但最慢</span></span></label>
                    <select id="whisperModel" name="whisperModel">
                        <option value="tiny">Tiny (最快，准确性最低)</option>
                        <option value="base">Base (快速且准确)</option>
                        <option value="small" selected>Small (平衡速度和准确性)</option>
                        <option value="medium">Medium (较慢但更准确)</option>
                        <option value="large">Large (最准确但最慢)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="promptTemplate">摘要模板</label>
                    <select id="promptTemplate" name="promptTemplate">
                        <option value="default课堂笔记">default课堂笔记 - 通用课堂笔记格式</option>
                        <option value="youtube_英文笔记">youtube_英文笔记 - 英文视频双语笔记格式</option>
                        <option value="youtube_结构化提取">youtube_结构化提取 - 结构化提取要点</option>
                        <option value="youtube_精炼提取">youtube_精炼提取 - 提取核心要点和精华</option>
                        <option value="youtube_专业课笔记">youtube_专业课笔记 - 教学视频专业笔记格式</option>
                        <option value="爆款短视频文案">爆款短视频文案 - 短视频内容文案风格</option>
                        <option value="youtube_视频总结">youtube_视频总结 - 综合性视频总结模板</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="customPrompt">自定义提示词 (可选)</label>
                    <textarea id="customPrompt" name="customPrompt" rows="4" placeholder="输入自定义的摘要提示词..."></textarea>
                    <small class="input-hint">如果填写将覆盖模板设置</small>
                </div>

                <button type="submit" class="btn"><i class="fas fa-play"></i> 开始处理</button>
            </form>

            <div id="urlProgress" class="progress-container">
                <div class="progress-bar">
                    <div id="urlProgressFill" class="progress-fill"></div>
                </div>
                <div id="urlStatusMessage" class="status-message status-info"></div>
            </div>
        </div>

        <!-- 本地音频处理标签页 -->
        <div id="audio" class="tab-content">
            <h2 class="section-title"><i class="fas fa-file-audio"></i> 处理本地音频文件</h2>
            <form id="audioForm" enctype="multipart/form-data" class="form-grid">
                <div class="form-group">
                    <label for="audioFile">选择音频文件</label>
                    <input type="file" id="audioFile" name="audioFile" accept=".mp3,.wav,.m4a,.mp4,.aac,.flac,.wma,.amr" required>
                    <small class="input-hint">支持格式：MP3, WAV, M4A, MP4, AAC, FLAC, WMA, AMR</small>
                </div>

                <div class="form-group">
                    <label for="audioWhisperModel">Whisper模型大小</label>
                    <select id="audioWhisperModel" name="audioWhisperModel">
                        <option value="tiny">Tiny (最快，准确性最低)</option>
                        <option value="base">Base (快速且准确)</option>
                        <option value="small" selected>Small (平衡速度和准确性)</option>
                        <option value="medium">Medium (较慢但更准确)</option>
                        <option value="large">Large (最准确但最慢)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="audioLanguage">音频语言 (可选)</label>
                    <select id="audioLanguage" name="audioLanguage">
                        <option value="">自动检测</option>
                        <option value="zh">中文 (zh)</option>
                        <option value="en">英语 (en)</option>
                        <option value="ja">日语 (ja)</option>
                        <option value="ko">韩语 (ko)</option>
                        <option value="fr">法语 (fr)</option>
                        <option value="de">德语 (de)</option>
                        <option value="es">西班牙语 (es)</option>
                        <option value="ru">俄语 (ru)</option>
                        <option value="ar">阿拉伯语 (ar)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="audioPromptTemplate">摘要模板</label>
                    <select id="audioPromptTemplate" name="audioPromptTemplate">
                        <option value="default课堂笔记">default课堂笔记 - 通用课堂笔记格式</option>
                        <option value="youtube_英文笔记">youtube_英文笔记 - 英文视频双语笔记格式</option>
                        <option value="youtube_结构化提取">youtube_结构化提取 - 结构化提取要点</option>
                        <option value="youtube_精炼提取">youtube_精炼提取 - 提取核心要点和精华</option>
                        <option value="youtube_专业课笔记">youtube_专业课笔记 - 教学视频专业笔记格式</option>
                        <option value="爆款短视频文案">爆款短视频文案 - 短视频内容文案风格</option>
                        <option value="youtube_视频总结">youtube_视频总结 - 综合性视频总结模板</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="audioCustomPrompt">自定义提示词 (可选)</label>
                    <textarea id="audioCustomPrompt" name="audioCustomPrompt" rows="4" placeholder="输入自定义的摘要提示词..."></textarea>
                    <small class="input-hint">如果填写将覆盖模板设置</small>
                </div>

                <button type="submit" class="btn"><i class="fas fa-upload"></i> 上传并处理</button>
            </form>

            <div id="audioProgress" class="progress-container">
                <div class="progress-bar">
                    <div id="audioProgressFill" class="progress-fill"></div>
                </div>
                <div id="audioStatusMessage" class="status-message status-info"></div>
            </div>
        </div>

        <!-- 批量处理标签页 -->
        <div id="batch" class="tab-content">
            <h2 class="section-title"><i class="fas fa-layer-group"></i> 批量处理音频文件</h2>
            <div class="form-grid">
                <p>批量处理功能允许您处理上传文件夹中的所有音频文件。</p>

                <div class="form-group">
                    <label for="batchUploadDir">上传文件夹路径</label>
                    <input type="text" id="batchUploadDir" name="batchUploadDir" value="uploads" placeholder="默认为 uploads 文件夹">
                    <small class="input-hint">请确保文件夹中包含支持的音频文件</small>
                </div>

                <div class="form-group">
                    <label for="batchWhisperModel">Whisper模型大小</label>
                    <select id="batchWhisperModel" name="batchWhisperModel">
                        <option value="tiny">Tiny (最快，准确性最低)</option>
                        <option value="base">Base (快速且准确)</option>
                        <option value="small" selected>Small (平衡速度和准确性)</option>
                        <option value="medium">Medium (较慢但更准确)</option>
                        <option value="large">Large (最准确但最慢)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="batchPromptTemplate">摘要模板</label>
                    <select id="batchPromptTemplate" name="batchPromptTemplate">
                        <option value="default课堂笔记">default课堂笔记 - 通用课堂笔记格式</option>
                        <option value="youtube_英文笔记">youtube_英文笔记 - 英文视频双语笔记格式</option>
                        <option value="youtube_结构化提取">youtube_结构化提取 - 结构化提取要点</option>
                        <option value="youtube_精炼提取">youtube_精炼提取 - 提取核心要点和精华</option>
                        <option value="youtube_专业课笔记">youtube_专业课笔记 - 教学视频专业笔记格式</option>
                        <option value="爆款短视频文案">爆款短视频文案 - 短视频内容文案风格</option>
                        <option value="youtube_视频总结">youtube_视频总结 - 综合性视频总结模板</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="batchCustomPrompt">自定义提示词 (可选)</label>
                    <textarea id="batchCustomPrompt" name="batchCustomPrompt" rows="4" placeholder="输入自定义的摘要提示词..."></textarea>
                    <small class="input-hint">如果填写将覆盖模板设置</small>
                </div>

                <button onclick="startBatchProcess()" class="btn"><i class="fas fa-forward"></i> 开始批量处理</button>
            </div>

            <div id="batchProgress" class="progress-container">
                <div class="progress-bar">
                    <div id="batchProgressFill" class="progress-fill"></div>
                </div>
                <div id="batchStatusMessage" class="status-message status-info"></div>
            </div>
        </div>

        <!-- API配置标签页 -->
        <div id="api_config" class="tab-content">
            <h2 class="section-title"><i class="fas fa-cog"></i> API配置</h2>
            <div class="form-grid">
                <p>在此配置您的AI服务API密钥，配置后将永久保存在本地。</p>

                <div class="form-group">
                    <label for="deepseekApiKey">DeepSeek API密钥</label>
                    <input type="password" id="deepseekApiKey" name="deepseekApiKey" placeholder="sk-xxxxxxxxxxxxxxxx">
                    <small class="input-hint">用于DeepSeek API服务的密钥</small>
                </div>

                <div class="form-group">
                    <label for="openaiApiKey">OpenAI API密钥 (可选)</label>
                    <input type="password" id="openaiApiKey" name="openaiApiKey" placeholder="sk-xxxxxxxxxxxxxxxx">
                    <small class="input-hint">用于OpenAI API服务的密钥</small>
                </div>

                <div class="form-group">
                    <label for="anthropicApiKey">Anthropic API密钥 (可选)</label>
                    <input type="password" id="anthropicApiKey" name="anthropicApiKey" placeholder="sk-ant-xxxxxxxxxxxxxxxx">
                    <small class="input-hint">用于Anthropic API服务的密钥</small>
                </div>

                <div class="form-group">
                    <label for="defaultModel">默认AI模型</label>
                    <select id="defaultModel" name="defaultModel">
                        <option value="deepseek-chat">DeepSeek Chat</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                        <option value="claude-3-haiku">Claude 3 Haiku</option>
                        <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        <option value="claude-3-opus">Claude 3 Opus</option>
                    </select>
                </div>

                <div class="action-buttons">
                    <button onclick="saveApiConfig()" class="btn"><i class="fas fa-save"></i> 保存配置</button>
                </div>

                <div id="apiConfigStatus" class="status-message" style="display:none;"></div>
            </div>
        </div>

        <!-- 查看结果标签页 -->
        <div id="results" class="tab-content">
            <h2 class="section-title"><i class="fas fa-file-alt"></i> 处理结果</h2>
            <div class="results-container" id="resultsSection">
                <div class="results-header">
                    <h3><i class="fas fa-folder-open"></i> 生成的总结文件</h3>
                    <button onclick="loadResults()" class="btn"><i class="fas fa-sync-alt"></i> 刷新列表</button>
                </div>
                <div class="results-list" id="resultsList">
                    <!-- 结果将通过JavaScript动态加载 -->
                </div>
            </div>
            <div id="noResultsMessage" class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>暂无处理结果</h3>
                <p>处理完成后文件将显示在此处</p>
            </div>
        </div>

        <!-- 任务历史标签页 -->
        <div id="history" class="tab-content">
            <h2 class="section-title"><i class="fas fa-history"></i> 任务历史记录</h2>
            <div class="results-container" id="historySection">
                <div class="results-header">
                    <h3><i class="fas fa-list"></i> 处理任务历史</h3>
                    <div>
                        <button onclick="loadTaskHistory()" class="btn"><i class="fas fa-sync-alt"></i> 刷新列表</button>
                        <button onclick="clearTaskHistory()" class="btn btn-error"><i class="fas fa-trash"></i> 清空历史</button>
                    </div>
                </div>
                <div class="results-list" id="historyList">
                    <!-- 历史记录将通过JavaScript动态加载 -->
                </div>
            </div>
            <div id="noHistoryMessage" class="empty-state">
                <i class="fas fa-history"></i>
                <h3>暂无任务历史记录</h3>
                <p>处理过的任务将显示在此处</p>
            </div>
        </div>
    </div>

    <script>
        // 页面加载时获取结果列表
        document.addEventListener('DOMContentLoaded', function() {
            // 加载可用的模型和模板（如果需要动态加载）
            loadModels();
            loadTemplates();
        });

        // 加载可用的Whisper模型
        async function loadModels() {
            try {
                const response = await fetch('/api/models');
                const data = await response.json();
                // 这里可以动态更新模型选择器，但目前使用静态选项
            } catch (error) {
                console.error('加载模型列表失败:', error);
            }
        }

        // 加载可用的提示词模板
        async function loadTemplates() {
            try {
                const response = await fetch('/api/prompt-templates');
                const data = await response.json();
                // 这里可以动态更新模板选择器，但目前使用静态选项
            } catch (error) {
                console.error('加载模板列表失败:', error);
            }
        }

        // 标签页切换功能
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                
                // 移除所有激活状态
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // 激活当前标签
                button.classList.add('active');
                document.getElementById(tabName).classList.add('active');

                // 如果切换到结果标签页，加载结果
                if (tabName === 'results') {
                    loadResults();
                }
                // 如果切换到历史标签页，加载历史
                else if (tabName === 'history') {
                    loadTaskHistory();
                }
            });
        });

        // 处理视频URL表单提交
        document.getElementById('urlForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const videoUrl = document.getElementById('videoUrl').value.trim();
            const model = document.getElementById('whisperModel').value;
            const promptTemplate = document.getElementById('promptTemplate').value;
            const customPrompt = document.getElementById('customPrompt').value.trim();

            if (!videoUrl) {
                alert('请输入视频URL');
                return;
            }

            // 显示进度条
            document.getElementById('urlProgress').style.display = 'block';
            document.getElementById('urlProgressFill').style.width = '5%';
            document.getElementById('urlStatusMessage').textContent = '正在发送请求...';
            document.getElementById('urlStatusMessage').className = 'status-message status-info';
            document.getElementById('urlStatusMessage').style.display = 'block';

            try {
                const response = await fetch('/process-url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: videoUrl,
                        model: model,
                        prompt_template: promptTemplate,
                        prompt: customPrompt || null
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || '请求失败');
                }

                const taskId = data.task_id;

                // 开始轮询任务状态
                await pollTaskStatus(taskId, 'url');
            } catch (error) {
                document.getElementById('urlStatusMessage').textContent = '错误: ' + error.message;
                document.getElementById('urlStatusMessage').className = 'status-message status-error';
                document.getElementById('urlStatusMessage').style.display = 'block';
            }
        });

        // 处理音频文件上传表单提交
        document.getElementById('audioForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData();
            const audioFile = document.getElementById('audioFile').files[0];
            const model = document.getElementById('audioWhisperModel').value;
            const language = document.getElementById('audioLanguage').value;
            const promptTemplate = document.getElementById('audioPromptTemplate').value;
            const customPrompt = document.getElementById('audioCustomPrompt').value.trim();

            if (!audioFile) {
                alert('请选择音频文件');
                return;
            }

            formData.append('file', audioFile);
            formData.append('model', model);
            if (language) formData.append('language', language);
            formData.append('prompt_template', promptTemplate);
            if (customPrompt) formData.append('prompt', customPrompt);

            // 显示进度条
            document.getElementById('audioProgress').style.display = 'block';
            document.getElementById('audioProgressFill').style.width = '5%';
            document.getElementById('audioStatusMessage').textContent = '正在上传文件...';
            document.getElementById('audioStatusMessage').className = 'status-message status-info';
            document.getElementById('audioStatusMessage').style.display = 'block';

            try {
                const response = await fetch('/upload-audio', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || '上传失败');
                }

                const taskId = data.task_id;

                // 开始轮询任务状态
                await pollTaskStatus(taskId, 'audio');
            } catch (error) {
                document.getElementById('audioStatusMessage').textContent = '错误: ' + error.message;
                document.getElementById('audioStatusMessage').className = 'status-message status-error';
                document.getElementById('audioStatusMessage').style.display = 'block';
            }
        });

        // 轮询任务状态
        async function pollTaskStatus(taskId, prefix) {
            let status;
            do {
                await new Promise(resolve => setTimeout(resolve, 2000)); // 每2秒查询一次

                try {
                    const response = await fetch(`/task-status/${taskId}`);
                    if (!response.ok) {
                        throw new Error(`获取任务状态失败: ${response.status}`);
                    }
                    status = await response.json();
                } catch (error) {
                    document.getElementById(prefix + 'StatusMessage').textContent = '错误: 无法获取任务状态 - ' + error.message;
                    document.getElementById(prefix + 'StatusMessage').className = 'status-message status-error';
                    document.getElementById(prefix + 'StatusMessage').style.display = 'block';
                    return;
                }

                const progressFill = document.getElementById(prefix + 'ProgressFill');
                const statusMessage = document.getElementById(prefix + 'StatusMessage');

                if (progressFill) {
                    progressFill.style.width = status.progress + '%';
                }

                if (statusMessage) {
                    statusMessage.textContent = status.message;

                    if (status.status === 'completed') {
                        statusMessage.className = 'status-message status-success';
                        statusMessage.innerHTML = status.message + '<br><a href="/download-result/' + encodeURIComponent(status.result_path) + '" target="_blank" class="btn"><i class="fas fa-download"></i> 点击下载结果</a>';
                    } else if (status.status === 'error') {
                        statusMessage.className = 'status-message status-error';
                    } else {
                        statusMessage.className = 'status-message status-info';
                    }

                    statusMessage.style.display = 'block';
                }
            } while (status.status === 'processing');
        }

        // 开始批量处理
        async function startBatchProcess() {
            const uploadDir = document.getElementById('batchUploadDir').value.trim() || 'uploads';
            const model = document.getElementById('batchWhisperModel').value;
            const promptTemplate = document.getElementById('batchPromptTemplate').value;
            const customPrompt = document.getElementById('batchCustomPrompt').value.trim();

            if (!uploadDir) {
                alert('请输入上传文件夹路径');
                return;
            }

            // 显示进度条
            document.getElementById('batchProgress').style.display = 'block';
            document.getElementById('batchProgressFill').style.width = '5%';
            document.getElementById('batchStatusMessage').textContent = '正在开始批量处理...';
            document.getElementById('batchStatusMessage').className = 'status-message status-info';
            document.getElementById('batchStatusMessage').style.display = 'block';

            try {
                const response = await fetch('/batch-process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        upload_dir: uploadDir,
                        model: model,
                        prompt_template: promptTemplate,
                        prompt: customPrompt || null
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || '批量处理请求失败');
                }

                const taskId = data.task_id;

                // 开始轮询任务状态
                await pollTaskStatus(taskId, 'batch');
            } catch (error) {
                document.getElementById('batchStatusMessage').textContent = '错误: ' + error.message;
                document.getElementById('batchStatusMessage').className = 'status-message status-error';
                document.getElementById('batchStatusMessage').style.display = 'block';
            }
        }

        // 加载处理结果
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const data = await response.json();

                const resultsList = document.getElementById('resultsList');
                const resultsSection = document.getElementById('resultsSection');
                const noResultsMessage = document.getElementById('noResultsMessage');

                if (data.results && data.results.length > 0) {
                    resultsList.innerHTML = '';
                    data.results.forEach(result => {
                        const resultItem = document.createElement('div');
                        resultItem.className = 'result-item';

                        // 格式化文件大小
                        const sizeInMB = (result.size / (1024 * 1024)).toFixed(2);

                        resultItem.innerHTML = `
                            <div class="result-info">
                                <div class="result-title">${result.filename}</div>
                                <div class="result-meta">修改时间: ${result.modified} | 大小: ${sizeInMB} MB</div>
                            </div>
                            <div class="result-actions">
                                <a href="/download-result/${encodeURIComponent(result.path)}" target="_blank">
                                    <button class="btn"><i class="fas fa-download"></i> 下载</button>
                                </a>
                            </div>
                        `;

                        resultsList.appendChild(resultItem);
                    });

                    resultsSection.style.display = 'block';
                    noResultsMessage.style.display = 'none';
                } else {
                    resultsSection.style.display = 'none';
                    noResultsMessage.style.display = 'block';
                }
            } catch (error) {
                console.error('加载结果列表失败:', error);
                document.getElementById('resultsList').innerHTML = '<div class="status-message status-error">加载结果失败: ' + error.message + '</div>';
            }
        }

        // 加载任务历史记录
        async function loadTaskHistory() {
            try {
                const response = await fetch('/api/task-history');
                const data = await response.json();

                const historyList = document.getElementById('historyList');
                const historySection = document.getElementById('historySection');
                const noHistoryMessage = document.getElementById('noHistoryMessage');

                if (data.history && data.history.length > 0) {
                    historyList.innerHTML = '';
                    data.history.forEach(task => {
                        const taskItem = document.createElement('div');
                        taskItem.className = 'result-item';

                        // 格式化任务类型
                        let taskTypeText = '';
                        switch(task.type) {
                            case 'video_url':
                                taskTypeText = '🔗 视频URL处理';
                                break;
                            case 'local_audio':
                                taskTypeText = '🎵 本地音频处理';
                                break;
                            case 'batch_process':
                                taskTypeText = '📦 批量处理';
                                break;
                            default:
                                taskTypeText = task.type;
                        }

                        // 格式化状态
                        let statusText = '';
                        let statusClass = '';
                        switch(task.status) {
                            case 'completed':
                                statusText = '已完成';
                                statusClass = 'completed';
                                break;
                            case 'error':
                                statusText = '失败';
                                statusClass = 'error';
                                break;
                            case 'processing':
                                statusText = '处理中';
                                statusClass = 'processing';
                                break;
                            default:
                                statusText = task.status;
                                statusClass = 'processing';
                        }

                        // 计算处理时长
                        let duration = 'N/A';
                        if (task.start_time && task.end_time) {
                            const start = new Date(task.start_time);
                            const end = new Date(task.end_time);
                            const diffSeconds = Math.round((end - start) / 1000);
                            if (diffSeconds < 60) {
                                duration = diffSeconds + '秒';
                            } else {
                                const diffMinutes = Math.round(diffSeconds / 60);
                                duration = diffMinutes + '分钟';
                            }
                        }

                        taskItem.innerHTML = `
                            <div class="result-info">
                                <div class="result-title">${taskTypeText}</div>
                                <div class="task-details">
                                    <span class="status-badge ${statusClass}"><i class="fas fa-circle"></i> ${statusText}</span>
                                </div>
                                <div class="task-input">
                                    输入: ${task.input.length > 50 ? task.input.substring(0, 50) + '...' : task.input}
                                </div>
                                <div class="task-meta">
                                    <span><i class="fas fa-microchip"></i> ${task.model}</span>
                                    <span><i class="fas fa-clock"></i> ${task.start_time}</span>
                                    <span><i class="fas fa-hourglass-half"></i> ${duration}</span>
                                </div>
                            </div>
                            <div class="result-actions">
                                ${task.result_path ?
                                    `<a href="/download-result/${encodeURIComponent(task.result_path)}" target="_blank">
                                        <button class="btn"><i class="fas fa-download"></i> 下载结果</button>
                                    </a>` :
                                    '<button class="btn" disabled><i class="fas fa-ban"></i> 无结果</button>'
                                }
                            </div>
                        `;

                        historyList.appendChild(taskItem);
                    });

                    historySection.style.display = 'block';
                    noHistoryMessage.style.display = 'none';
                } else {
                    historySection.style.display = 'none';
                    noHistoryMessage.style.display = 'block';
                }
            } catch (error) {
                console.error('加载任务历史失败:', error);
                document.getElementById('historyList').innerHTML = '<div class="status-message status-error">加载任务历史失败: ' + error.message + '</div>';
            }
        }

        // 清空任务历史记录
        async function clearTaskHistory() {
            if (!confirm('确定要清空所有任务历史记录吗？此操作不可撤销。')) {
                return;
            }

            try {
                const response = await fetch('/api/task-history', {
                    method: 'DELETE'
                });

                if (response.ok) {
                    loadTaskHistory(); // 重新加载历史记录
                    alert('任务历史记录已清空');
                } else {
                    const data = await response.json();
                    alert('清空历史记录失败: ' + (data.detail || '未知错误'));
                }
            } catch (error) {
                alert('清空历史记录失败: ' + error.message);
            }
        }

        // 保存API配置
        async function saveApiConfig() {
            const deepseekApiKey = document.getElementById('deepseekApiKey').value;
            const openaiApiKey = document.getElementById('openaiApiKey').value;
            const anthropicApiKey = document.getElementById('anthropicApiKey').value;
            const defaultModel = document.getElementById('defaultModel').value;

            const config = {
                api_keys: {
                    deepseek: deepseekApiKey,
                    openai: openaiApiKey,
                    anthropic: anthropicApiKey
                },
                default_model: defaultModel
            };

            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(config)
                });

                const result = await response.json();

                const statusElement = document.getElementById('apiConfigStatus');
                if (response.ok) {
                    statusElement.textContent = '配置保存成功！';
                    statusElement.className = 'status-message status-success';
                    statusElement.style.display = 'block';

                    // 清空输入框中的密钥（出于安全考虑）
                    document.getElementById('deepseekApiKey').value = '';
                    document.getElementById('openaiApiKey').value = '';
                    document.getElementById('anthropicApiKey').value = '';
                } else {
                    statusElement.textContent = '配置保存失败: ' + result.detail;
                    statusElement.className = 'status-message status-error';
                    statusElement.style.display = 'block';
                }

                // 3秒后隐藏状态信息
                setTimeout(() => {
                    statusElement.style.display = 'none';
                }, 3000);
            } catch (error) {
                const statusElement = document.getElementById('apiConfigStatus');
                statusElement.textContent = '保存配置时发生错误: ' + error.message;
                statusElement.className = 'status-message status-error';
                statusElement.style.display = 'block';

                setTimeout(() => {
                    statusElement.style.display = 'none';
                }, 3000);
            }
        }

        // 页面加载时加载API配置
        window.addEventListener('load', function() {
            loadApiConfig();
        });

        // 加载API配置
        async function loadApiConfig() {
            try {
                const response = await fetch('/api/config');
                if (response.ok) {
                    const config = await response.json();

                    // 注意：出于安全原因，我们不会在前端显示实际的API密钥
                    // 但我们可以设置占位符来显示密钥是否已配置
                    if (config.api_keys && config.api_keys.deepseek) {
                        document.getElementById('deepseekApiKey').placeholder = '[已配置 - 输入新密钥以更新]';
                    }
                    if (config.api_keys && config.api_keys.openai) {
                        document.getElementById('openaiApiKey').placeholder = '[已配置 - 输入新密钥以更新]';
                    }
                    if (config.api_keys && config.api_keys.anthropic) {
                        document.getElementById('anthropicApiKey').placeholder = '[已配置 - 输入新密钥以更新]';
                    }

                    if (config.default_model) {
                        document.getElementById('defaultModel').value = config.default_model;
                    }
                }
            } catch (error) {
                console.error('加载API配置失败:', error);
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
        except:
            pass  # 如果JSON解析失败，使用表单参数

    # 确保URL不为空
    if not url:
        raise HTTPException(status_code=422, detail="URL是必需的")
    task_id = str(uuid.uuid4())
    
    # 确定使用哪个提示词
    prompt_to_use = prompt if prompt else prompt_templates.get(prompt_template, prompt_templates["default课堂笔记"])
    
    # 生成输出文件路径
    auto_filename = generate_filename(url, has_summary=True, is_local=False)
    output_path = os.path.join("summaries", auto_filename)
    
    # 初始化任务状态
    task_status[task_id] = {"status": "processing", "progress": 0, "message": "初始化..."}
    
    # 在后台线程中运行处理任务
    thread = threading.Thread(
        target=process_video_url_task,
        args=(task_id, url, model, prompt_to_use, output_path)
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
    prompt_to_use = prompt if prompt else prompt_templates.get(prompt_template, prompt_templates["default课堂笔记"])
    
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
    prompt_to_use = prompt if prompt else prompt_templates.get(prompt_template, prompt_templates["default课堂笔记"])
    
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
    from fastapi.responses import FileResponse

    # 解码文件路径
    import urllib.parse
    decoded_path = urllib.parse.unquote(file_path)

    if not os.path.exists(decoded_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=decoded_path,
        media_type='text/markdown',
        filename=os.path.basename(decoded_path)
    )


@app.get("/api/prompt-templates")
async def get_prompt_templates():
    """获取所有可用的提示词模板"""
    return {"templates": [
        {"name": "default课堂笔记", "description": "通用课堂笔记格式，适合大多数教学视频"},
        {"name": "youtube_英文笔记", "description": "专门用于英文视频的双语笔记格式"},
        {"name": "youtube_结构化提取", "description": "以结构化方式提取要点"},
        {"name": "youtube_精炼提取", "description": "提取核心要点和精华"},
        {"name": "youtube_专业课笔记", "description": "适用于教学视频的专业笔记格式"},
        {"name": "爆款短视频文案", "description": "适用于短视频内容的文案风格"},
        {"name": "youtube_视频总结", "description": "综合性视频总结模板"}
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
async def get_config():
    """获取API配置"""
    try:
        config_data = {
            "api_keys": {
                "deepseek": bool(config_manager.get_api_key("deepseek")),
                "openai": bool(config_manager.get_api_key("openai")),
                "anthropic": bool(config_manager.get_api_key("anthropic"))
            },
            "default_model": config_manager.get_default_model()
        }
        return config_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@app.post("/api/config")
async def update_config(request: Request):
    """更新API配置"""
    try:
        data = await request.json()

        # 更新API密钥
        api_keys = data.get("api_keys", {})
        for provider, key in api_keys.items():
            if key:  # 只有当提供了密钥时才更新
                set_api_key(provider, key)

        # 更新默认模型
        default_model = data.get("default_model")
        if default_model:
            config_manager.set_default_model(default_model)

        return {"message": "配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)