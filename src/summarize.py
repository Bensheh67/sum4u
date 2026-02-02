"""
summarize.py
GPT 摘要模块。
"""

from typing import Optional
import requests

from .prompts import prompt_default, prompt_templates

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
        api_key = "DEEPSEEK_API_KEY_REMOVED"
        p = prompt if prompt else prompt_default
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