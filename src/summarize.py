"""
summarize.py
AI 摘要模块 - 支持多种 API 提供商。
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
    "anthropic": "https://api.anthropic.com/v1/messages"
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
    调用 AI API 对转录文本进行结构化总结。
    自动分段摘要，单段不超过 15000 字，多段时自动整合。
    :param text: 需要总结的文本
    :param prompt: 自定义摘要提示词（可选）
    :param model: AI 模型名
    :param provider: API 提供商 ('deepseek', 'openai', 'anthropic')
    :return: 结构化摘要文本
    """
    def call_api(chunk, is_merge=False):
        api_key = get_api_key(provider)
        if not api_key:
            raise ValueError(f"未找到 {provider} 的 API 密钥，请在 config.json 中设置")

        p = prompt if prompt else prompt_default

        if is_merge:
            # 整合多个分段总结
            p = f"""你是内容整合专家，负责将多个分段总结整合为一个统一的结构化笔记。

【任务要求】
1. 阅读以下多个分段总结
2. 识别并合并重复的内容（如多个"知识结构图"、多个"全文总结"等）
3. 按时间轴或逻辑顺序重新组织分段总结
4. 确保输出只有一个统一的标题、一个知识结构图、一个全文总结、一个术语表
5. 保持原有的 Markdown 格式

【输出格式】
直接输出整合后的 Markdown 文档，不要包含任何说明性文字。

---
分段总结内容：
{chunk}
"""
        else:
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

        elif provider == "anthropic":
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
            raise ValueError(f"不支持的 API 提供商：{provider}")

    # 分段处理
    chunks = split_text(text, 15000)
    print(f"文本分为{len(chunks)}段，每段不超过 15000 字，使用 {provider} API")

    if len(chunks) == 1:
        # 只有一段，直接总结
        summaries = [call_api(chunks[0])]
    else:
        # 多段：先分段总结，再整合
        print("分段总结中...")
        partial_summaries = [call_api(chunk) for chunk in chunks]
        print("整合分段总结...")
        # 将分段总结合并为一段文本进行整合
        combined = '\n\n--- 分隔符 ---\n\n'.join(partial_summaries)
        summaries = [call_api(combined, is_merge=True)]

    summary_text = '\n\n'.join(summaries)
    # 如拼接后仍超长，递归再次摘要
    if len(summary_text) > 15000:
        print("摘要结果仍超长，递归再次摘要...")
        return summarize_text(summary_text, prompt, model, provider)
    return summary_text
