"""
keyframe_selector.py
AI 关键帧选择模块 - 分析转录文本让 AI 选择最佳截图时间点。
"""

import json
import re
from typing import List, Dict, Optional

from .config import get_api_key


DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def format_transcript_with_timestamps(segments: List[Dict]) -> str:
    """
    将 Whisper 输出的 segments 格式化为带时间戳的转录文本

    Args:
        segments: whisper transcribe 返回的 segments 列表

    Returns:
        格式化后的转录文本
    """
    formatted_lines = []

    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()

        start_str = _seconds_to_timestamp(start)
        end_str = _seconds_to_timestamp(end)

        formatted_lines.append(f"[{start_str}-{end_str}] {text}")

    return "\n".join(formatted_lines)


def _seconds_to_timestamp(seconds: float) -> str:
    """秒数转换为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


PROMPT_KEYFRAME_SELECTION = """
你是视频内容分析专家，负责从视频转录文本中识别最具代表性的关键帧时间点。

【任务】
分析提供的视频转录文本（包括时间戳），识别8-12个最具代表性的关键帧时间点。

【识别标准】
1. 话题转换点 - 新主题/章节开始时
2. 核心要点呈现 - 重要概念、数据、结论首次出现
3. 视觉焦点时刻 - 描述特定场景、演示、图表的时刻
4. 情感/高潮点 - 观众可能有强烈反应的时刻
5. 总结/强调时刻 - 作者重复强调的内容

【输出要求】
返回JSON格式的时间点列表：
{{
  "keyframes": [
    {{"timestamp": 90.5, "reason": "介绍核心概念", "relevance": 5}},
    ...
  ]
}}

【防幻觉约束】
- 只选择转录文本中明确涵盖的时间范围
- 不要编造不存在的内容
- 时间点必须在视频时长范围内
- timestamp 必须是数字（秒），不能是字符串
"""


def select_keyframes(transcript: str, video_duration: float = None,
                    model: str = "deepseek-chat") -> List[Dict]:
    """
    使用 AI 分析转录文本，选择关键帧时间点

    Args:
        transcript: 格式化后的带时间戳转录文本
        video_duration: 视频总时长（秒），用于校验时间点
        model: DeepSeek 模型名

    Returns:
        关键帧列表，每项包含 timestamp, reason, relevance
    """
    import requests

    prompt = PROMPT_KEYFRAME_SELECTION + "\n\n---\n转录文本如下：\n" + transcript

    api_key = get_api_key("deepseek")
    if not api_key:
        raise ValueError("DeepSeek API key not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "stream": False
    }

    response = requests.post(
        DEEPSEEK_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()

    print(f"[DEBUG] select_keyframes AI返回原始内容长度: {len(content)}")
    print(f"[DEBUG] select_keyframes AI返回内容前200字符: {content[:200]}")

    try:
        result = json.loads(content)
        print(f"[DEBUG] select_keyframes JSON解析成功, keyframes数量: {len(result.get('keyframes', []))}")
    except json.JSONDecodeError:
        print(f"[DEBUG] select_keyframes JSON解析失败，尝试正则提取...")
        # 尝试从代码块中提取 JSON
        match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1))
                print(f"[DEBUG] select_keyframes 从代码块中提取JSON成功")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] 代码块JSON解析失败: {e}")
                result = None
        else:
            # 尝试直接匹配 JSON 对象（处理嵌套括号）
            try:
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                if json_match:
                    result = json.loads(json_match.group(0))
                    print(f"[DEBUG] select_keyframes 正则提取JSON成功")
                else:
                    print(f"[DEBUG] select_keyframes 未找到JSON对象")
                    result = None
            except Exception as e:
                print(f"[DEBUG] select_keyframes 正则提取失败: {e}")
                result = None

        if result is None:
            print(f"[ERROR] select_keyframes 无法解析AI返回内容，返回空列表")
            return []

    keyframes = result.get("keyframes", [])

    validated = []
    for kf in keyframes:
        ts = kf.get("timestamp", 0)
        if isinstance(ts, (int, float)) and ts >= 0:
            if video_duration is None or ts <= video_duration:
                validated.append({
                    "timestamp": float(ts),
                    "reason": kf.get("reason", "")[:50],
                    "relevance": min(5, max(1, int(kf.get("relevance", 3))))
                })

    validated.sort(key=lambda x: x["timestamp"])
    return validated[:12]
