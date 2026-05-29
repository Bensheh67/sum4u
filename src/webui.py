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
from fastapi.responses import HTMLResponse
import threading
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
from src.utils import generate_filename
from src.batch_processor import process_batch
from src.douyin_handler import is_douyin_url, clean_douyin_url
from src.config import config_manager
from src.video_classifier import classify_video

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


def process_video_url_task(task_id: str, video_url: str, model: str, prompt_to_use: str, output_path: str, with_screenshots: bool = False, auto_template: bool = False):
    """处理视频URL的后台任务

    Args:
        auto_template: 如果为 True，自动根据视频类型选择最合适的模板
    """
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

                # 自动视频类型分类
                if auto_template:
                    print(f"[{task_id}] 视频类型分析...")
                    classification = classify_video(video_title, "")
                    print(f"[{task_id}]    检测类型: {classification.video_type} (置信度: {classification.confidence})")
                    print(f"[{task_id}]    推理: {classification.reasoning}")
                    auto_prompt_key = classification.suggested_prompt_key
                    if auto_prompt_key in prompt_templates:
                        prompt_to_use = prompt_templates[auto_prompt_key]
                        print(f"[{task_id}]    使用模板: {auto_prompt_key}")
                    task_status[task_id] = {"status": "processing", "progress": 5, "message": f"视频类型: {classification.video_type}，使用模板: {auto_prompt_key}"}

                # 验证视频文件是否存在
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

            # 自动视频类型分类
            if auto_template:
                print(f"[{task_id}] 视频类型分析...")
                classification = classify_video(video_title, "")
                print(f"[{task_id}]    检测类型: {classification.video_type} (置信度: {classification.confidence})")
                print(f"[{task_id}]    推理: {classification.reasoning}")
                auto_prompt_key = classification.suggested_prompt_key
                if auto_prompt_key in prompt_templates:
                    prompt_to_use = prompt_templates[auto_prompt_key]
                    print(f"[{task_id}]    使用模板: {auto_prompt_key}")
                task_status[task_id] = {"status": "processing", "progress": 12, "message": f"视频类型: {classification.video_type}，使用模板: {auto_prompt_key}"}

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
        summary_dir = os.path.dirname(summary_file_path) or "summaries"
        os.makedirs(summary_dir, exist_ok=True)

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
  <title>summary4u — 音视频总结工具</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Source+Sans+3:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    /* ===== DESIGN TOKENS (from DESIGN.md) ===== */
    :root {
      --color-primary: #0D9488;
      --color-primary-hover: #0F766E;
      --color-primary-light: #CCFBF1;
      --color-secondary: #14B8A6;
      --color-bg: #FFFFFF;
      --color-surface: #F8FAFC;
      --color-surface-hover: #F1F5F9;
      --color-border: #E2E8F0;
      --color-border-strong: #CBD5E1;
      --color-text: #1E293B;
      --color-text-secondary: #64748B;
      --color-text-muted: #94A3B8;
      --color-success: #10B981;
      --color-warning: #F59E0B;
      --color-error: #EF4444;
      --color-info: #3B82F6;

      --font-display: 'Instrument Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-body: 'Source Sans 3', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', 'SF Mono', Consolas, monospace;

      --radius-sm: 4px;
      --radius-md: 8px;
      --radius-lg: 12px;

      --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
      --shadow-md: 0 4px 12px rgba(0,0,0,0.06);

      --sidebar-width: 240px;
      --header-height: 56px;
      --max-width: 1200px;

      --space-2xs: 2px;
      --space-xs: 4px;
      --space-sm: 8px;
      --space-md: 16px;
      --space-lg: 24px;
      --space-xl: 32px;
      --space-2xl: 48px;

      --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
      --ease-in: cubic-bezier(0.7, 0, 0.84, 0);
    }

    /* ===== RESET ===== */
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

    html {
      font-size: 16px;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    body {
      font-family: var(--font-body);
      font-size: 16px;
      line-height: 1.6;
      color: var(--color-text);
      background: var(--color-bg);
      min-height: 100vh;
    }

    /* ===== LAYOUT ===== */
    .app-layout {
      display: flex;
      min-height: 100vh;
    }

    /* ===== SIDEBAR ===== */
    .sidebar {
      width: var(--sidebar-width);
      background: var(--color-surface);
      border-right: 1px solid var(--color-border);
      display: flex;
      flex-direction: column;
      position: fixed;
      top: 0;
      left: 0;
      height: 100vh;
      z-index: 100;
    }

    .sidebar-header {
      padding: var(--space-lg) var(--space-lg) var(--space-md);
      border-bottom: 1px solid var(--color-border);
    }

    .logo {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .logo-icon {
      width: 32px;
      height: 32px;
      background: var(--color-primary);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-family: var(--font-display);
      font-size: 16px;
      font-weight: 700;
      flex-shrink: 0;
    }

    .logo-text {
      font-family: var(--font-display);
      font-size: 17px;
      font-weight: 700;
      color: var(--color-text);
      letter-spacing: -0.3px;
    }

    .logo-sub {
      font-size: 11px;
      color: var(--color-text-muted);
      font-weight: 400;
      margin-top: 1px;
    }

    .sidebar-nav {
      flex: 1;
      padding: var(--space-md) var(--space-sm);
      overflow-y: auto;
    }

    .nav-section {
      margin-bottom: var(--space-lg);
    }

    .nav-section-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 0 var(--space-sm);
      margin-bottom: var(--space-xs);
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px var(--space-sm);
      border-radius: var(--radius-md);
      color: var(--color-text-secondary);
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s var(--ease-out);
      text-decoration: none;
      border: none;
      background: none;
      width: 100%;
      text-align: left;
    }

    .nav-item:hover {
      background: var(--color-surface-hover);
      color: var(--color-text);
    }

    .nav-item.active {
      background: var(--color-primary-light);
      color: var(--color-primary);
    }

    .nav-item svg {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      opacity: 0.7;
    }

    .nav-item.active svg { opacity: 1; }

    .nav-badge {
      margin-left: auto;
      background: var(--color-primary);
      color: white;
      font-size: 11px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 10px;
      min-width: 20px;
      text-align: center;
    }

    .sidebar-footer {
      padding: var(--space-md) var(--space-lg);
      border-top: 1px solid var(--color-border);
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .user-avatar {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 13px;
      font-weight: 600;
      font-family: var(--font-display);
    }

    .user-name {
      font-size: 13px;
      font-weight: 500;
      color: var(--color-text);
    }

    .user-role {
      font-size: 11px;
      color: var(--color-text-muted);
    }

    /* ===== MAIN CONTENT ===== */
    .main-content {
      flex: 1;
      margin-left: var(--sidebar-width);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    /* ===== HEADER ===== */
    .header {
      height: var(--header-height);
      border-bottom: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 var(--space-lg);
      background: var(--color-bg);
      position: sticky;
      top: 0;
      z-index: 50;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }

    .page-title {
      font-family: var(--font-display);
      font-size: 16px;
      font-weight: 600;
      color: var(--color-text);
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .header-btn {
      width: 44px;
      height: 44px;
      border-radius: var(--radius-md);
      border: 1px solid var(--color-border);
      background: var(--color-bg);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--color-text-secondary);
      transition: all 0.15s var(--ease-out);
    }

    .header-btn:hover {
      background: var(--color-surface);
      color: var(--color-text);
      border-color: var(--color-border-strong);
    }

    .header-btn svg {
      width: 18px;
      height: 18px;
    }

    /* ===== TABS ===== */
    .tabs {
      display: flex;
      gap: var(--space-xs);
      padding: var(--space-md) var(--space-lg);
      border-bottom: 1px solid var(--color-border);
      background: var(--color-bg);
      overflow-x: auto;
    }

    .tab {
      padding: var(--space-sm) var(--space-md);
      border: none;
      background: none;
      font-family: var(--font-body);
      font-size: 14px;
      font-weight: 500;
      color: var(--color-text-secondary);
      cursor: pointer;
      border-radius: var(--radius-md);
      transition: all 0.15s var(--ease-out);
      white-space: nowrap;
    }

    .tab:hover {
      color: var(--color-text);
      background: var(--color-surface);
    }

    .tab.active {
      color: var(--color-primary);
      background: var(--color-primary-light);
    }

    /* ===== CONTENT ===== */
    .content {
      flex: 1;
      padding: var(--space-lg);
      max-width: var(--max-width);
    }

    /* ===== PANELS ===== */
    .panel {
      display: none;
    }

    .panel.active {
      display: block;
      animation: fadeIn 0.2s var(--ease-out);
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* ===== CARDS ===== */
    .card {
      background: var(--color-bg);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: var(--space-lg);
      box-shadow: var(--shadow-sm);
    }

    .card + .card {
      margin-top: var(--space-md);
    }

    .card-header {
      margin-bottom: var(--space-lg);
    }

    .card-title {
      font-family: var(--font-display);
      font-size: 15px;
      font-weight: 600;
      color: var(--color-text);
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .card-title svg {
      width: 18px;
      height: 18px;
      color: var(--color-primary);
    }

    /* ===== FORMS ===== */
    .form-row {
      margin-bottom: var(--space-md);
    }

    .form-label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      color: var(--color-text);
      margin-bottom: 6px;
    }

    .form-hint {
      font-size: 12px;
      color: var(--color-text-muted);
      margin-top: var(--space-xs);
    }

    .form-row-inline {
      display: flex;
      align-items: center;
      gap: var(--space-md);
    }

    .input-wrap {
      position: relative;
    }

    .input {
      width: 100%;
      height: 40px;
      padding: 0 12px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      font-family: var(--font-body);
      font-size: 14px;
      color: var(--color-text);
      background: var(--color-bg);
      transition: all 0.15s var(--ease-out);
    }

    .input:focus {
      outline: none;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
    }

    .input::placeholder {
      color: var(--color-text-muted);
    }

    .input-with-btn {
      display: flex;
      gap: var(--space-sm);
    }

    .input-with-btn .input {
      flex: 1;
    }

    /* ===== BUTTONS ===== */
    .btn {
      height: 40px;
      padding: 0 var(--space-md);
      border-radius: var(--radius-md);
      font-family: var(--font-body);
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s var(--ease-out);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      border: none;
      text-decoration: none;
    }

    .btn svg {
      width: 16px;
      height: 16px;
    }

    .btn-primary {
      background: var(--color-primary);
      color: white;
    }

    .btn-primary:hover {
      background: var(--color-primary-hover);
    }

    .btn-secondary {
      background: var(--color-surface);
      color: var(--color-text);
      border: 1px solid var(--color-border);
    }

    .btn-secondary:hover {
      background: var(--color-surface-hover);
      border-color: var(--color-border-strong);
    }

    .btn-ghost {
      background: transparent;
      color: var(--color-text-secondary);
    }

    .btn-ghost:hover {
      background: var(--color-surface);
      color: var(--color-text);
    }

    .btn-block {
      width: 100%;
    }

    .btn-sm {
      height: 32px;
      padding: 0 var(--space-sm);
      font-size: 13px;
    }

    /* ===== SELECT ===== */
    .select {
      width: 100%;
      height: 40px;
      padding: 0 36px 0 12px;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      font-family: var(--font-body);
      font-size: 14px;
      color: var(--color-text);
      background: var(--color-bg);
      cursor: pointer;
      appearance: none;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 10px center;
      transition: all 0.15s var(--ease-out);
    }

    .select:focus {
      outline: none;
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
    }

    /* ===== CHECKBOX ===== */
    .checkbox-label {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      cursor: pointer;
      font-size: 14px;
      color: var(--color-text);
    }

    .checkbox-label input[type="checkbox"] {
      width: 16px;
      height: 16px;
      accent-color: var(--color-primary);
      cursor: pointer;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
    }

    /* ===== FORM GRID ===== */
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--space-md);
    }

    .form-grid-full {
      grid-column: 1 / -1;
    }

    /* ===== TOGGLE ===== */
    .toggle-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 0;
    }

    .toggle-info {
      flex: 1;
    }

    .toggle-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--color-text);
    }

    .toggle-desc {
      font-size: 12px;
      color: var(--color-text-muted);
      margin-top: 2px;
    }

    .toggle {
      width: 44px;
      height: 24px;
      background: var(--color-border-strong);
      border-radius: 12px;
      position: relative;
      cursor: pointer;
      transition: background 0.2s var(--ease-out);
      border: none;
    }

    .toggle.active {
      background: var(--color-primary);
    }

    .toggle-knob {
      width: 20px;
      height: 20px;
      background: white;
      border-radius: 50%;
      position: absolute;
      top: 2px;
      left: 2px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
      transition: transform 0.2s var(--ease-out);
    }

    .toggle.active .toggle-knob {
      transform: translateX(20px);
    }

    /* ===== DIVIDER ===== */
    .divider {
      height: 1px;
      background: var(--color-border);
      margin: var(--space-md) 0;
    }

    /* ===== PROGRESS ===== */
    .progress-area {
      display: none;
      margin-top: var(--space-md);
    }

    .progress-area.show {
      display: block;
    }

    .progress-bar {
      height: 4px;
      background: var(--color-surface);
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: var(--space-sm);
      border: 1px solid var(--color-border);
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
      width: 0%;
      transition: width 0.4s var(--ease-out);
    }

    .status-msg {
      padding: var(--space-sm) var(--space-sm);
      border-radius: var(--radius-md);
      font-size: 13px;
      display: none;
      border: 1px solid;
    }

    .status-msg.show { display: block; }

    .status-success {
      background: rgba(16, 185, 129, 0.1);
      color: var(--color-success);
      border-color: var(--color-success);
    }

    .status-error {
      background: rgba(239, 68, 68, 0.1);
      color: var(--color-error);
      border-color: var(--color-error);
    }

    .status-info {
      background: rgba(59, 130, 246, 0.1);
      color: var(--color-info);
      border-color: var(--color-info);
    }

    /* ===== RESULT CARDS ===== */
    .result-card {
      background: var(--color-bg);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      overflow: hidden;
      box-shadow: var(--shadow-sm);
    }

    .result-card-header {
      padding: var(--space-md) var(--space-lg);
      border-bottom: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .result-video-info {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
    }

    .result-video-thumb {
      width: 56px;
      height: 36px;
      background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 11px;
      font-weight: 500;
      font-family: var(--font-mono);
    }

    .result-video-meta h3 {
      font-family: var(--font-display);
      font-size: 14px;
      font-weight: 600;
      color: var(--color-text);
      margin-bottom: 2px;
    }

    .result-video-meta span {
      font-size: 12px;
      color: var(--color-text-muted);
    }

    .result-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--color-success);
      font-weight: 500;
    }

    .result-status-dot {
      width: 6px;
      height: 6px;
      background: var(--color-success);
      border-radius: 50%;
    }

    .result-card-body {
      padding: var(--space-lg);
    }

    .stats-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: var(--space-sm);
      margin-bottom: var(--space-md);
    }

    .stat-item {
      background: var(--color-surface);
      border-radius: var(--radius-md);
      padding: var(--space-sm) var(--space-sm);
      text-align: center;
    }

    .stat-value {
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 700;
      color: var(--color-text);
    }

    .stat-label {
      font-size: 11px;
      color: var(--color-text-muted);
      margin-top: 2px;
    }

    .result-section {
      margin-bottom: var(--space-md);
    }

    .result-section:last-child {
      margin-bottom: 0;
    }

    .result-section-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: var(--space-xs);
    }

    .result-tags {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-xs);
    }

    .tag {
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      background: var(--color-surface);
      border-radius: 20px;
      font-size: 12px;
      color: var(--color-text-secondary);
      font-weight: 500;
    }

    .tag-primary {
      background: var(--color-primary-light);
      color: var(--color-primary);
    }

    /* ===== HISTORY LIST ===== */
    .history-list {
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }

    .history-item {
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      padding: var(--space-sm) var(--space-md);
      background: var(--color-bg);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all 0.15s var(--ease-out);
    }

    .history-item:hover {
      border-color: var(--color-border-strong);
      background: var(--color-surface);
    }

    .history-icon {
      width: 36px;
      height: 36px;
      background: var(--color-surface);
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-text-secondary);
      flex-shrink: 0;
    }

    .history-icon svg {
      width: 16px;
      height: 16px;
    }

    .history-info {
      flex: 1;
      min-width: 0;
    }

    .history-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--color-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .history-meta {
      font-size: 11px;
      color: var(--color-text-muted);
      margin-top: 2px;
    }

    .history-badge {
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      flex-shrink: 0;
    }

    .badge-success {
      background: rgba(16, 185, 129, 0.12);
      color: var(--color-success);
    }

    .badge-error {
      background: rgba(239, 68, 68, 0.12);
      color: var(--color-error);
    }

    .badge-processing {
      background: rgba(59, 130, 246, 0.12);
      color: var(--color-info);
    }

    /* ===== EMPTY STATE ===== */
    .empty-state {
      text-align: center;
      padding: var(--space-2xl) var(--space-lg);
      color: var(--color-text-muted);
    }

    .empty-state-icon {
      width: 56px;
      height: 56px;
      margin: 0 auto var(--space-md);
      background: var(--color-surface);
      border-radius: var(--radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .empty-state-icon svg {
      width: 24px;
      height: 24px;
      color: var(--color-text-muted);
    }

    .empty-state-title {
      font-family: var(--font-display);
      font-size: 15px;
      font-weight: 600;
      color: var(--color-text);
      margin-bottom: var(--space-xs);
    }

    .empty-state-text {
      font-size: 13px;
      color: var(--color-text-muted);
      max-width: 280px;
      margin: 0 auto;
    }

    /* ===== CONFIG GRID ===== */
    .config-grid {
      display: grid;
      gap: var(--space-md);
    }

    .config-item {
      display: flex;
      flex-direction: column;
      gap: var(--space-xs);
    }

    .config-item label {
      font-size: 13px;
      font-weight: 500;
      color: var(--color-text);
    }

    .config-item small {
      font-size: 12px;
      color: var(--color-text-muted);
    }

    .config-item small a {
      color: var(--color-primary);
      text-decoration: none;
    }

    .config-item small a:hover {
      text-decoration: underline;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
      .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s var(--ease-out);
      }

      .sidebar.open {
        transform: translateX(0);
      }

      .main-content {
        margin-left: 0;
      }

      .form-grid {
        grid-template-columns: 1fr;
      }

      .stats-row {
        grid-template-columns: repeat(2, 1fr);
      }

      .header {
        padding: 0 var(--space-md);
      }

      .content {
        padding: var(--space-md);
      }

      .tabs {
        padding: var(--space-sm) var(--space-md);
      }

      .mode-switcher {
        bottom: 80px;
        right: 12px;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
      }
    }

    /* ===== DARK MODE ===== */
    body.dark {
      --color-bg: #0F172A;
      --color-surface: #1E293B;
      --color-surface-hover: #334155;
      --color-border: #334155;
      --color-border-strong: #475569;
      --color-text: #F1F5F9;
      --color-text-secondary: #94A3B8;
      --color-text-muted: #64748B;
    }

    body.dark .sidebar {
      background: #1E293B;
    }

    body.dark .result-video-thumb {
      background: linear-gradient(135deg, #334155 0%, #475569 100%);
    }

    /* ===== MODE SWITCHER ===== */
    .mode-switcher {
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: var(--color-bg);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      padding: 10px 14px;
      box-shadow: var(--shadow-md);
      display: flex;
      align-items: center;
      gap: var(--space-sm);
      z-index: 1000;
      font-size: 12px;
      color: var(--color-text-secondary);
    }
  </style>
</head>
<body>
  <div class="app-layout">
    <!-- SIDEBAR -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">S</div>
          <div>
            <div class="logo-text">summary4u</div>
            <div class="logo-sub">音视频总结工具</div>
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-label">工作区</div>
          <button class="nav-item active" data-panel="url">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
              <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
            </svg>
            视频链接
          </button>
          <button class="nav-item" data-panel="audio">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18V5l12-2v13"></path>
              <circle cx="6" cy="18" r="3"></circle>
              <circle cx="18" cy="16" r="3"></circle>
            </svg>
            本地文件
          </button>
          <button class="nav-item" data-panel="batch">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            批量处理
          </button>
          <button class="nav-item" data-panel="results">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            输出文件
          </button>
          <button class="nav-item" data-panel="history">
            历史记录
            <span class="nav-badge">3</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </button>
        </div>

        <div class="nav-section">
          <div class="nav-section-label">设置</div>
          <button class="nav-item" data-panel="config">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            API 配置
          </button>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">B</div>
          <div>
            <div class="user-name">Ben</div>
            <div class="user-role">Pro plan</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="main-content">
      <!-- HEADER -->
      <header class="header">
        <div class="header-left">
          <h1 class="page-title">视频链接处理</h1>
        </div>
        <div class="header-right">
          <button class="header-btn" title="通知">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </button>
          <button class="header-btn" title="帮助">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </button>
        </div>
      </header>

      <!-- TABS -->
      <nav class="tabs">
        <button class="tab active" data-tab="url">URL处理</button>
        <button class="tab" data-tab="audio">本地文件</button>
        <button class="tab" data-tab="batch">批量处理</button>
        <button class="tab" data-tab="results">输出</button>
        <button class="tab" data-tab="history">历史</button>
        <button class="tab" data-tab="config">配置</button>
      </nav>

      <!-- CONTENT -->
      <div class="content">
        <!-- URL PANEL -->
        <div id="panel-url" class="panel active">
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                </svg>
                输入视频链接
              </div>
            </div>

            <div class="form-row">
              <div class="form-label">视频 URL</div>
              <div class="input-with-btn">
                <input type="url" class="input" id="videoUrl" placeholder="粘贴 YouTube、Bilibili、抖音链接">
                <button class="btn btn-primary" onclick="processUrl()">提取</button>
              </div>
              <div class="form-hint">支持 YouTube、Bilibili、抖音、TikTok 等平台</div>
            </div>

            <div class="divider"></div>

            <div class="form-grid">
              <div class="form-row">
                <div class="form-label">转录模型</div>
                <select class="select" id="whisperModel">
                  <option value="tiny">Tiny (最快，准确率最低)</option>
                  <option value="base">Base (快速准确)</option>
                  <option value="small" selected>Small (推荐)</option>
                  <option value="medium">Medium (更准确)</option>
                  <option value="large">Large (最准确，最慢)</option>
                </select>
              </div>

              <div class="form-row">
                <div class="form-label">摘要模板</div>
                <select class="select" id="promptTemplate">
                  <option>default 课堂笔记</option>
                  <option>youtube_结构化提取</option>
                  <option>youtube_英文笔记</option>
                  <option>youtube_专业课笔记</option>
                  <option>youtube_精炼提取</option>
                  <option>youtube_视频总结</option>
                  <option>爆款短视频文案</option>
                </select>
              </div>

              <div class="form-row form-grid-full">
                <div class="toggle-row">
                  <div class="toggle-info">
                    <div class="toggle-label">自动选择模板</div>
                    <div class="toggle-desc">根据视频类型自动选择最优模板</div>
                  </div>
                  <button class="toggle" id="autoTemplateToggle" onclick="this.classList.toggle('active')">
                    <div class="toggle-knob"></div>
                  </button>
                </div>
              </div>

              <div class="form-row form-grid-full">
                <div class="toggle-row">
                  <div class="toggle-info">
                    <div class="toggle-label">启用视频截图</div>
                    <div class="toggle-desc">AI 自动选择关键帧插入总结</div>
                  </div>
                  <button class="toggle" id="screenshotToggle" onclick="this.classList.toggle('active')">
                    <div class="toggle-knob"></div>
                  </button>
                </div>
              </div>
            </div>

            <div style="margin-top: var(--space-lg);">
              <button class="btn btn-primary btn-block" onclick="processUrl()">开始总结</button>
            </div>

            <div id="urlProgress" class="progress-area">
              <div class="progress-bar">
                <div class="progress-fill" id="urlProgressFill"></div>
              </div>
              <div class="status-msg" id="urlStatusMsg"></div>
            </div>
          </div>

          <!-- RESULT PREVIEW -->
          <div class="card" style="margin-top: var(--space-md);">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                最近完成
              </div>
              <button class="btn btn-ghost btn-sm">查看全部</button>
            </div>

            <div class="result-card">
              <div class="result-card-header">
                <div class="result-video-info">
                  <div class="result-video-thumb">YT</div>
                  <div class="result-video-meta">
                    <h3>DeepLearning AI - Transformer入门教程</h3>
                    <span>youtube.com · 18分钟 · 刚刚完成</span>
                  </div>
                </div>
                <div class="result-status">
                  <div class="result-status-dot"></div>
                  完成
                </div>
              </div>
              <div class="result-card-body">
                <div class="stats-row">
                  <div class="stat-item">
                    <div class="stat-value">2,847</div>
                    <div class="stat-label">转录字数</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">486</div>
                    <div class="stat-label">总结字数</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">12</div>
                    <div class="stat-label">关键帧</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">3分22秒</div>
                    <div class="stat-label">处理耗时</div>
                  </div>
                </div>

                <div class="result-section">
                  <div class="result-section-label">内容标签</div>
                  <div class="result-tags">
                    <span class="tag tag-primary">学习视频</span>
                    <span class="tag">教程</span>
                    <span class="tag">AI/ML</span>
                    <span class="tag">Transformer</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="history-list" style="margin-top: var(--space-md);">
              <div class="history-item">
                <div class="history-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  </svg>
                </div>
                <div class="history-info">
                  <div class="history-title">Bilibili - 产品经理入门第一课</div>
                  <div class="history-meta">bilibili.com · 25分钟前</div>
                </div>
                <span class="history-badge badge-success">完成</span>
              </div>
              <div class="history-item">
                <div class="history-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 18V5l12-2v13"></path>
                    <circle cx="6" cy="18" r="3"></circle>
                    <circle cx="18" cy="16" r="3"></circle>
                  </svg>
                </div>
                <div class="history-info">
                  <div class="history-title">播客录制 - 创业融资分享会.mp3</div>
                  <div class="history-meta">本地文件 · 1小时前</div>
                </div>
                <span class="history-badge badge-success">完成</span>
              </div>
            </div>
          </div>
        </div>

        <!-- AUDIO PANEL -->
        <div id="panel-audio" class="panel">
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 18V5l12-2v13"></path>
                  <circle cx="6" cy="18" r="3"></circle>
                  <circle cx="18" cy="16" r="3"></circle>
                </svg>
                上传本地音频
              </div>
            </div>

            <div class="form-row">
              <div class="form-label">选择文件</div>
              <input type="file" class="input" id="audioFile" accept=".mp3,.wav,.m4a,.mp4,.aac,.flac,.wma,.amr" style="padding: 8px 12px; height: auto;">
              <div class="form-hint">支持 MP3, WAV, M4A, AAC, FLAC 等格式</div>
            </div>

            <div class="form-grid">
              <div class="form-row">
                <div class="form-label">转录模型</div>
                <select class="select" id="audioModel">
                  <option value="small" selected>Small (推荐)</option>
                  <option value="tiny">Tiny</option>
                  <option value="base">Base</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
              </div>

              <div class="form-row">
                <div class="form-label">音频语言</div>
                <select class="select" id="audioLanguage">
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
            </div>

            <div style="margin-top: var(--space-lg);">
              <button class="btn btn-primary btn-block">上传并处理</button>
            </div>
          </div>
        </div>

        <!-- BATCH PANEL -->
        <div id="panel-batch" class="panel">
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                  <line x1="8" y1="21" x2="16" y2="21"></line>
                  <line x1="12" y1="17" x2="12" y2="21"></line>
                </svg>
                批量处理
              </div>
            </div>

            <div class="form-row">
              <div class="form-label">上传目录</div>
              <input type="text" class="input" id="batchDir" value="uploads" placeholder="uploads">
              <div class="form-hint">指定包含音频文件的文件夹路径</div>
            </div>

            <div class="form-grid">
              <div class="form-row">
                <div class="form-label">转录模型</div>
                <select class="select">
                  <option value="small" selected>Small (推荐)</option>
                  <option value="tiny">Tiny</option>
                  <option value="base">Base</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
              </div>

              <div class="form-row">
                <div class="form-label">摘要模板</div>
                <select class="select">
                  <option>default 课堂笔记</option>
                  <option>youtube_结构化提取</option>
                  <option>youtube_英文笔记</option>
                </select>
              </div>
            </div>

            <div style="margin-top: var(--space-lg);">
              <button class="btn btn-primary btn-block">开始批量处理</button>
            </div>
          </div>
        </div>

        <!-- RESULTS PANEL -->
        <div id="panel-results" class="panel">
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                生成文件
              </div>
              <button class="btn btn-secondary btn-sm">刷新</button>
            </div>

            <div class="history-list">
              <div class="history-item">
                <div class="history-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                </div>
                <div class="history-info">
                  <div class="history-title">DeepLearning_Transformer总结.md</div>
                  <div class="history-meta">2.4 MB · 刚刚</div>
                </div>
                <button class="btn btn-secondary btn-sm">下载</button>
              </div>
            </div>
          </div>
        </div>

        <!-- HISTORY PANEL -->
        <div id="panel-history" class="panel">
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
                处理历史
              </div>
              <div style="display: flex; gap: var(--space-sm);">
                <button class="btn btn-secondary btn-sm">刷新</button>
                <button class="btn btn-secondary btn-sm" style="color: var(--color-error);">清空</button>
              </div>
            </div>

            <div class="history-list">
              <div class="history-item">
                <div class="history-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  </svg>
                </div>
                <div class="history-info">
                  <div class="history-title">DeepLearning AI - Transformer入门教程</div>
                  <div class="history-meta">youtube.com · small · 刚刚</div>
                </div>
                <span class="history-badge badge-success">完成</span>
              </div>
              <div class="history-item">
                <div class="history-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  </svg>
                </div>
                <div class="history-info">
                  <div class="history-title">Bilibili - 产品经理入门第一课</div>
                  <div class="history-meta">bilibili.com · small · 25分钟前</div>
                </div>
                <span class="history-badge badge-success">完成</span>
              </div>
              <div class="history-item">
                <div class="history-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M9 18V5l12-2v13"></path>
                    <circle cx="6" cy="18" r="3"></circle>
                  </svg>
                </div>
                <div class="history-info">
                  <div class="history-title">播客录制 - 创业融资分享会.mp3</div>
                  <div class="history-meta">本地文件 · base · 1小时前</div>
                </div>
                <span class="history-badge badge-success">完成</span>
              </div>
            </div>
          </div>
        </div>

        <!-- CONFIG PANEL -->
        <div id="panel-config" class="panel">
          <div class="card">
            <div class="card-header">
              <div class="card-title">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                API 配置
              </div>
            </div>

            <div class="config-grid">
              <div class="config-item">
                <label for="apiTikhub">TikHub API</label>
                <input type="password" class="input" id="apiTikhub" placeholder="抖音/TikTok 下载用">
                <small><a href="https://user.tikhub.io/users/signin" target="_blank">获取 API Key</a></small>
              </div>

              <div class="config-item">
                <label for="apiDeepseek">DeepSeek API</label>
                <input type="password" class="input" id="apiDeepseek" placeholder="AI 摘要用">
                <small><a href="https://platform.deepseek.com/api_keys" target="_blank">获取 API Key</a></small>
              </div>

              <div class="config-item">
                <label for="apiOpenai">OpenAI API（可选）</label>
                <input type="password" class="input" id="apiOpenai" placeholder="备用">
              </div>

              <div class="config-item">
                <label for="apiAnthropic">Anthropic API（可选）</label>
                <input type="password" class="input" id="apiAnthropic" placeholder="备用">
              </div>
            </div>

            <div style="margin-top: var(--space-lg); display: flex; justify-content: flex-end; gap: var(--space-sm);">
              <button class="btn btn-secondary">测试连接</button>
              <button class="btn btn-primary">保存配置</button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- MODE SWITCHER -->
  <div class="mode-switcher">
    <span>Light</span>
    <button class="toggle" id="darkModeToggle" onclick="document.body.classList.toggle('dark'); this.classList.toggle('active');">
      <div class="toggle-knob"></div>
    </button>
    <span>Dark</span>
  </div>

  <script>
    // Tab navigation
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const panelId = 'panel-' + tab.dataset.tab;
        document.getElementById(panelId).classList.add('active');
        updatePageTitle(tab.textContent);
      });
    });

    // Sidebar navigation
    document.querySelectorAll('.nav-item[data-panel]').forEach(item => {
      item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        const panelId = 'panel-' + item.dataset.panel;
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        document.getElementById(panelId).classList.add('active');
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        const matchingTab = document.querySelector(`.tab[data-tab="${item.dataset.panel}"]`);
        if (matchingTab) matchingTab.classList.add('active');
        updatePageTitle(item.textContent.trim());
      });
    });

    function updatePageTitle(title) {
      document.querySelector('.page-title').textContent = title;
    }

    // Process URL
    function processUrl() {
      const url = document.getElementById('videoUrl').value;
      if (!url) {
        showProgress('url', '请输入视频URL', 'error');
        return;
      }
      showProgress('url', '正在发送请求...', 'info');
    }

    function showProgress(prefix, msg, type) {
      const progressEl = document.getElementById(prefix + 'Progress');
      const fillEl = document.getElementById(prefix + 'ProgressFill');
      const msgEl = document.getElementById(prefix + 'StatusMsg');
      progressEl.classList.add('show');
      fillEl.style.width = '5%';
      msgEl.className = 'status-msg status-' + type + ' show';
      msgEl.textContent = msg;
    }

    // Dark mode toggle
    const darkToggle = document.getElementById('darkModeToggle');
    darkToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark');
    });
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)



@app.post("/process-url")
async def process_video_url_endpoint(
    url: str = Form(None),
    model: str = Form(default="small"),
    prompt_template: str = Form(default="default 课堂笔记"),
    prompt: Optional[str] = Form(default=None),
    with_screenshots: bool = Form(default=False),
    auto_template: bool = Form(default=False),
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
            auto_template = body.get("auto_template", auto_template)
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
        args=(task_id, url, model, prompt_to_use, output_path, with_screenshots, auto_template)
    )
    thread.start()

    return {"task_id": task_id}


@app.post("/upload-audio")
async def upload_audio_endpoint(
    file: UploadFile = File(...),
    model: str = Form(default="small"),
    language: Optional[str] = Form(default=None),
    prompt_template: str = Form(default="default 课堂笔记"),
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
    prompt_template: str = Form(default="default 课堂笔记"),
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