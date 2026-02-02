"""
summarize.py
AI 摘要模块 - 支持多种API提供商。
"""

from typing import Optional
import requests
import os

from .prompts import prompt_default, prompt_templates
from .config import get_api_key

# API URL 配置
API_URLS = {
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages"  # 这里使用示例URL，实际需要根据Anthropic API格式调整
}


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


def summarize_text(text: str, prompt: Optional[str] = None, model: str = "deepseek-chat", provider: str = "deepseek") -> str:
    """
    调用AI API对转录文本进行结构化总结。
    自动分段摘要，单段不超过15000字。
    :param text: 需要总结的文本
    :param prompt: 自定义摘要提示词（可选）
    :param model: AI模型名
    :param provider: API提供商 ('deepseek', 'openai', 'anthropic')
    :return: 结构化摘要文本
    """
    def call_api(chunk):
        api_key = get_api_key(provider)
        if not api_key:
            raise ValueError(f"未找到 {provider} 的API密钥，请在 config.json 中设置")

        p = prompt if prompt else prompt_default
        p = p + "\n" + chunk

        if provider == "deepseek" or provider == "openai":
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
            response = requests.post(API_URLS[provider], headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        # 注意：Anthropic API 格式可能需要单独处理
        elif provider == "anthropic":
            # Anthropic API 的调用方式不同，这里只是示例
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": p}
                ],
                "max_tokens": 4096,
                "temperature": 0.6
            }
            response = requests.post(API_URLS[provider], headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"].strip()

        else:
            raise ValueError(f"不支持的API提供商: {provider}")

    # 分段处理
    chunks = split_text(text, 15000)
    print(f"文本分为{len(chunks)}段，每段不超过15000字，使用 {provider} API")
    summaries = [call_api(chunk) for chunk in chunks]
    summary_text = '\n\n'.join(summaries)
    # 如拼接后仍超长，递归摘要
    if len(summary_text) > 15000:
        print("摘要结果仍超长，递归再次摘要...")
        return summarize_text(summary_text, prompt, model, provider)
    return summary_text