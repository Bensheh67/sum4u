"""
video_classifier.py
视频类型分类器 — 根据视频元数据（标题、描述）自动判断视频类型，
选择对应的总结模板。
"""

from dataclasses import dataclass
from typing import Literal, Optional

# 视频类型定义
VideoType = Literal["learning", "tutorial", "review", "interview"]

# 类型到 prompt 模板的映射
PROMPT_KEY_MAP: dict[VideoType, str] = {
    "learning": "课堂内容",
    "tutorial": "短视频素材",
    "review": "精炼摘要",
    "interview": "精炼摘要",
}

# 关键词规则定义
TYPE_RULES: dict[VideoType, list[dict]] = {
    "tutorial": [
        {"patterns": ["教程", "入门", "从零开始", "how to", "教学", "手把手", "实战", "一步步"], "weight": 1.0},
        {"patterns": ["学会", "掌握", "精通", "教学", "讲解", "传授"], "weight": 0.8},
    ],
    "review": [
        {"patterns": ["评测", "测评", "体验", "对比", "vs", "vs.", "横评", "测评", "试用"], "weight": 1.0},
        {"patterns": ["怎么样", "好不好", "值得买", "推荐", "种草", "拔草"], "weight": 0.7},
    ],
    "interview": [
        {"patterns": ["访谈", "对话", "圆桌", "采访", "对话", "会客厅", "聊聊"], "weight": 1.0},
        {"patterns": ["嘉宾", "主持人", "说", "表示", "认为", "指出"], "weight": 0.6},
    ],
    "learning": [
        {"patterns": ["学习", "理解", "掌握", "概念", "原理", "科普", "解释", "知识"], "weight": 1.0},
        {"patterns": ["为什么", "是什么", "如何", "怎样", "介绍", "解析"], "weight": 0.7},
    ],
}


@dataclass
class VideoClassification:
    """视频分类结果"""
    video_type: VideoType  # 主类型：learning | tutorial | review | interview
    confidence: float  # 0.0 - 1.0
    reasoning: str  # 为什么分类到这种类型
    suggested_prompt_key: str  # 对应使用的 prompt 模板 key
    secondary_type: Optional[VideoType] = None  # 辅类型（混合视频时）
    extension_suggestion: str = ""  # 扩展建议（供 Phase 3 使用）

    def __post_init__(self):
        self.suggested_prompt_key = PROMPT_KEY_MAP.get(self.video_type, "综合总结")
        if not self.extension_suggestion:
            self.extension_suggestion = self._get_extension_suggestion()

    def _get_extension_suggestion(self) -> str:
        """根据类型返回扩展建议"""
        suggestions = {
            "learning": "建议添加相关概念的上游基础知识链接和下游深入学习路径",
            "tutorial": "建议添加实战练习项目和延伸学习资源",
            "review": "建议添加类似产品对比和相关评测链接",
            "interview": "建议添加嘉宾背景和相关演讲链接",
        }
        return suggestions.get(self.video_type, "")


def _match_patterns(text: str, rules: list[dict]) -> tuple[float, list[str]]:
    """
    根据规则匹配文本，返回匹配的权重和匹配的关键词列表。
    """
    text_lower = text.lower()
    total_weight = 0.0
    matched = []

    for rule in rules:
        for pattern in rule["patterns"]:
            if pattern.lower() in text_lower:
                total_weight += rule["weight"]
                matched.append(pattern)

    return total_weight, matched


def classify_video(
    title: str,
    description: str = "",
    transcript_preview: Optional[str] = None
) -> VideoClassification:
    """
    根据视频元数据分类视频类型。

    Args:
        title: 视频标题
        description: 视频描述（可选）
        transcript_preview: 转录文本预览（可选，用于辅助判断）

    Returns:
        VideoClassification: 包含类型、置信度、推理过程和建议的 prompt 模板
    """
    # 合并文本用于分析
    combined_text = f"{title} {description}"
    if transcript_preview:
        # 只取前 500 字符作为预览，避免过长
        combined_text += f" {transcript_preview[:500]}"

    # 计算每种类型的匹配得分
    scores: dict[VideoType, tuple[float, list[str]]] = {}
    for video_type, rules in TYPE_RULES.items():
        score, matched = _match_patterns(combined_text, rules)
        scores[video_type] = (score, matched)

    # 找出最高分类型和次高分类型（用于混合类型检测）
    sorted_scores = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
    best_type = sorted_scores[0][0]
    best_score = sorted_scores[0][1][0]
    best_matched = sorted_scores[0][1][1]

    # 检查是否有次高分（达到一定阈值，视为混合类型）
    secondary_type: Optional[VideoType] = None
    if len(sorted_scores) >= 2:
        second_type, (second_score, _) = sorted_scores[1]
        # 如果第二名得分 >= 第一名的 60%，视为混合类型
        if best_score > 0 and second_score >= best_score * 0.6:
            secondary_type = second_type

    # 计算置信度
    # 基准：0.4 为最低阈值，1.0 为最高
    # 有匹配时：0.4 + 0.6 * min(score / 3.0, 1.0)
    # 无匹配时：默认 0.5
    if best_score > 0:
        confidence = min(0.4 + 0.6 * (best_score / 3.0), 1.0)
    else:
        confidence = 0.5
        best_type = "learning"  # 默认类型
        best_matched = []

    # 构建推理说明
    if best_matched:
        reasoning = f"根据标题/描述中的关键词: {', '.join(best_matched[:5])}"
    else:
        reasoning = "未检测到明确类型特征，使用默认分类"

    # 低置信度降级策略
    if confidence < 0.4:
        reasoning += "（置信度低，默认使用 learning 模板）"

    # 混合类型说明
    if secondary_type:
        reasoning += f"（混合类型：主类型={best_type}，辅类型={secondary_type}）"

    return VideoClassification(
        video_type=best_type,
        confidence=round(confidence, 2),
        reasoning=reasoning,
        suggested_prompt_key=PROMPT_KEY_MAP[best_type],
        secondary_type=secondary_type
    )


def get_prompt_for_type(video_type: VideoType) -> str:
    """获取指定视频类型对应的 prompt 模板名称。"""
    return PROMPT_KEY_MAP.get(video_type, "综合总结")


if __name__ == "__main__":
    # 简单测试
    test_cases = [
        ("【教程】Python 从零开始入门完整视频", ""),
        ("iPhone 15 Pro Max 全面评测体验", ""),
        ("对话张一鸣：关于创业和人生", ""),
        ("深度学习反向传播算法详解", ""),
        ("如何用 ChatGPT 提升工作效率", ""),
    ]

    print("=== 视频分类器测试 ===\n")
    for title, desc in test_cases:
        result = classify_video(title, desc)
        print(f"标题: {title}")
        print(f"  类型: {result.video_type}")
        print(f"  置信度: {result.confidence}")
        print(f"  推理: {result.reasoning}")
        print(f"  推荐模板: {result.suggested_prompt_key}")
        print()