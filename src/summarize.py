"""
summarize.py
GPT 摘要模块。
"""

from typing import Optional, List, Dict, Tuple
import requests
from pathlib import Path

from .config import get_api_key
from .prompts import prompt_templates, prompt_with_screenshots

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def split_text(text, max_len=15000):
    """将文本按最大长度分段，优先按段落分割。"""
    if len(text) <= max_len:
        return [text]
    parts = []
    paragraphs = text.split('\n')
    buf = ''
    for para in paragraphs:
        if len(buf) + len(para) + 1 > max_len:
            parts.append(buf)
            buf = para
        else:
            buf += ('\n' if buf else '') + para
    if buf:
        parts.append(buf)
    return parts


def summarize_text(text: str, prompt: Optional[str] = None, model: str = "deepseek-chat") -> str:
    """
    调用 DeepSeek API 对转录文本进行结构化总结。
    自动分段摘要，单段不超过15000字。
    :param text: 需要总结的文本
    :param prompt: 自定义摘要提示词（可选）
    :param model: DeepSeek 模型名，默认 deepseek-chat
    :return: 结构化摘要文本
    """
    def call_api(chunk):
        api_key = get_api_key("deepseek")
        p = prompt if prompt else prompt_templates["短视频知识"]
        p = p + "\n" + chunk
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": p}
            ],
            "temperature": 0.6,
            "stream": False
        }
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    # 分段处理
    chunks = split_text(text, 15000)
    print(f"文本分为{len(chunks)}段，每段不超过15000字")
    summaries = [call_api(chunk) for chunk in chunks]
    summary_text = '\n\n'.join(summaries)
    # 如拼接后仍超长，递归摘要
    if len(summary_text) > 15000:
        print("摘要结果仍超长，递归再次摘要...")
        return summarize_text(summary_text, prompt, model)
    return summary_text


def summarize_with_screenshots(
    transcript_data: Dict,
    video_path: str,
    summary_name: str,
    prompt_key: str = "短视频知识",
    model: str = "deepseek-chat"
) -> Tuple[str, List[Dict], Path]:
    """
    生成带截图引用的总结

    Args:
        transcript_data: 转录数据，包含 "text" 和 "segments"
        video_path: 视频文件路径
        summary_name: 总结文件夹名称
        prompt_key: 提示词模板key
        model: DeepSeek 模型名

    Returns:
        (markdown_summary, extracted_frames_info, summary_dir)
    """
    from .video import (
        ensure_summary_dir,
        ensure_screenshots_dir,
        extract_multiple_frames,
        get_video_duration
    )
    from .keyframe_selector import format_transcript_with_timestamps, select_keyframes

    transcript_text = transcript_data.get("text", "")
    segments = transcript_data.get("segments", [])

    # 1. 创建总结文件夹
    summary_dir = ensure_summary_dir(summary_name)

    # 2. 获取视频时长
    video_duration = get_video_duration(video_path)

    # 3. AI 选择关键帧
    if segments:
        formatted_transcript = format_transcript_with_timestamps(segments)
        ai_keyframes = select_keyframes(formatted_transcript, video_duration, model)
    else:
        ai_keyframes = []

    # 4. 创建截图目录
    screenshots_dir = ensure_screenshots_dir(summary_name)

    # 5. 提取截图
    extracted_frames = extract_multiple_frames(
        video_path=video_path,
        timestamps=ai_keyframes,
        output_dir=screenshots_dir,
        video_duration=video_duration
    )

    # 6. 生成带截图引用的总结
    base_prompt = prompt_templates.get(prompt_key, prompt_templates["短视频知识"])
    screenshot_prompt = prompt_with_screenshots(base_prompt)

    summary = summarize_text(transcript_text, prompt=screenshot_prompt, model=model)

    # 7. 在总结中插入截图引用
    summary_with_refs = insert_screenshot_references(summary, extracted_frames)

    return summary_with_refs, extracted_frames, summary_dir


def insert_screenshot_references(summary: str, frames: List[Dict]) -> str:
    """
    在总结中插入截图引用

    策略：
    1. 在每个主要章节（## 标题）后添加一张相关截图
    2. 如果截图多余章节，在末尾添加截图章节
    """
    if not frames:
        return summary

    lines = summary.split('\n')
    result_lines = []
    frame_index = 0

    for line in lines:
        result_lines.append(line)

        if line.startswith('## ') and frame_index < len(frames):
            frame = frames[frame_index]
            img_ref = f'\n![{frame["reason"]}](screenshots/{frame["filename"]})\n'
            result_lines.append(img_ref)
            frame_index += 1

    if frame_index < len(frames):
        result_lines.append('\n\n## 视频截图\n')
        for frame in frames[frame_index:]:
            img_ref = f'![{frame["reason"]}](screenshots/{frame["filename"]})\n'
            result_lines.append(img_ref)

    return '\n'.join(result_lines)