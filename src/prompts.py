"""
prompts.py
该文件存储所有用于摘要的提示词模板。
"""

prompt_default="""
# 视频课程笔记生成 Prompt

请基于提供的视频转录文字，生成一份结构化的学习笔记。要求如下：

## 输出要求

### 1. 文档头部信息
- 视频标题
- 视频来源（YouTube/Bilibili）
- 视频链接（如有）
- 视频时长
- 笔记生成日期

### 2. 全文主题和内容框架 
根据文章结构内容使用合适的Mermaid图表， Mermaid mindmap 或 flowchart 语法，生成视频内容的思维导图，要求：
- 清晰展示主题和各级子主题的层级关系
- 包含所有重要知识点模块
- 使用简洁的关键词标注
- 仔细确认语法，确保无错误

### 3. 内容分段总结
对视频内容进行时间轴分段，每个分段包含：
- **时间戳**：该段内容对应的视频时间
- **段落标题**：该段的核心主题（10字以内）
- **核心内容**：
  - 高度还原讲师的表达逻辑和语言风格
  - 保留关键术语、概念定义、示例说明
  - 提炼核心观点，但不改变原意
  - 包含重要的代码示例、公式或图表说明（如有）
- **关键要点**：用 bullet points 列出该段的核心知识点（3-5个）

### 4. 全文总结
- **核心观点**：整个视频的主要论点或教学目标（3-5句话）
- **关键收获**：最重要的知识点或技能（5-8个 bullet points）
- **适用场景**：这些知识可以应用在哪些实际场景
- **延伸学习**：建议的后续学习方向或相关主题

### 5. 术语表（可选）
如果视频涉及专业术语，列出：
- 术语名称
- 简明解释
- 在视频中的使用场景

## 内容要求

1. **准确性**：忠实还原视频内容，不添加视频中未提及的信息
2. **结构化**：使用 Markdown 标题层级清晰组织内容
3. **可读性**：
   - 使用代码块标注代码示例
   - 使用引用块标注重要观点
   - 使用表格整理对比性内容
   - 使用列表突出要点
4. **完整性**：涵盖视频的所有重要内容，不遗漏关键信息

## 输出格式

以 Markdown (.md) 格式输出，文件名格式：`[视频标题]_学习笔记_[日期].md`

---

"""

prompt_1 = """
# 英文视频课程笔记生成 Prompt

Please generate structured learning notes based on the provided video transcript. Requirements:

## Output Requirements

### 1. Document Header
- Video Title
- Source (YouTube/Bilibili)
- Video Link (if available)
- Duration
- Note Creation Date

### 2. Content Framework (Mermaid Diagram)
Generate a Mermaid mindmap or flowchart to visualize the video's content structure:
- Clearly show the hierarchy of main topics and subtopics
- Include all important knowledge modules
- Use concise keywords for labeling

### 3. Segmented Content Summary
Divide the video content by timeline, each segment includes:
- **Timestamp**: Video time for this segment
- **Section Title**: Core topic (within 10 words)
- **Core Content**:
  - Faithfully restore the instructor's logic and language style
  - Preserve key terms, concept definitions, and examples
  - Extract core viewpoints without changing the original meaning
  - Include important code examples, formulas, or diagrams (if any)
  - **Keep all content in English**
- **Key Points**: List 3-5 core knowledge points in bullet format

### 4. Overall Summary
- **Core Arguments**: Main points or teaching objectives (3-5 sentences)
- **Key Takeaways**: Most important knowledge or skills (5-8 bullet points)
- **Use Cases**: Practical scenarios where this knowledge applies
- **Further Learning**: Suggested follow-up topics or learning directions

### 5. Bilingual Glossary (REQUIRED)
For technical terms and key concepts:
- **English Term**
- **Chinese Translation** (中文翻译)
- **Definition/Explanation** (in English)
- **Context in Video** (usage scenario)

Format:
```
| English Term | 中文翻译 | Definition | Context |
|--------------|---------|------------|---------|
| ... | ... | ... | ... |
```

### 6. Key Vocabulary Section
Extract 20-30 important words/phrases with:
- **English Expression**
- **中文含义**
- **Example Sentence** (from video context)

## Content Requirements

1. **Accuracy**: Faithfully represent video content without adding unmentioned information
2. **Structure**: Use clear Markdown heading hierarchy
3. **Readability**:
   - Use code blocks for code examples
   - Use blockquotes for important viewpoints
   - Use tables for comparative content
   - Use lists to highlight key points
4. **Completeness**: Cover all important content without omitting key information
5. **Language**: 
   - Main content in **English**
   - Add Chinese translations for technical terms
   - Bilingual glossary required

## Output Format

Output in Markdown (.md) format
Filename: `[Video_Title]_Notes_[Date].md`

---

**Please process the following video transcript:**

[Paste video transcript here]
"""

prompt_2 = """
# 视频内容结构化提取 Prompt

请将提供的视频转录文本进行结构化提取，生成清晰的知识框架。

## 输出要求

### 1. 核心概念提取
- 列出视频中提到的所有核心概念和术语
- 为每个概念提供简洁的定义
- 按重要性排序

### 2. 逻辑框架梳理
- 识别视频内容的逻辑结构（如：问题-解决方案、因果关系、时间顺序等）
- 生成内容大纲，体现层级关系
- 使用Mermaid语法创建流程图或思维导图

### 3. 关键信息提取
- 重要数据和统计信息
- 关键时间点和事件
- 重要人物和角色
- 关键引用或名言

### 4. 实用技巧/方法论
- 视频中提到的实用技巧
- 可操作的步骤或方法
- 实践建议

### 5. 问题与解答
- 视频中提到的问题
- 对应的解决方案或答案

### 6. 扩展思考
- 视频内容的延伸应用
- 可能的争议点或不同观点
- 进一步研究的方向

## 格式要求
- 使用Markdown格式
- 使用清晰的标题层级
- 用列表和表格组织信息
- 保持原文的准确性
"""

prompt_3 = """
# 视频内容精炼提取 Prompt

请对提供的视频转录文本进行精炼提取，提取最核心的要点和精华内容。

## 输出要求

### 1. 核心信息摘要
- 用2-3句话概括视频的核心内容
- 突出最重要的观点或发现

### 2. 关键要点列表
- 提取3-7个最重要的要点
- 每个要点用1-2句话表述
- 按重要性排序

### 3. 实用价值提取
- 最有价值的实用信息
- 可立即应用的建议或技巧
- 关键行动要点

### 4. 金句摘录
- 视频中最精彩或有启发性的语句
- 最具洞察力的观点

### 5. 核心数据/事实
- 最重要的数据、统计或事实
- 关键的时间、地点、人物信息

## 格式要求
- 极简风格，避免冗余
- 使用要点列表形式
- 保持信息的准确性
- 突出精华内容
"""

prompt_4 = """
# 专业课程笔记 Prompt

请将提供的视频转录文本整理为专业课程笔记，适合学术或专业学习使用。

## 输出要求

### 1. 课程信息
- 课程名称
- 讲师信息
- 课程时间
- 课程目标

### 2. 知识体系构建
- 主题概念定义
- 理论框架梳理
- 概念之间的关系图
- 相关知识点链接

### 3. 详细内容笔记
- 按时间或逻辑顺序记录
- 重要定义和解释
- 推导过程或分析步骤
- 例题或案例分析

### 4. 学习重点
- 本节课的核心知识点
- 需要掌握的技能
- 重点难点解析

### 5. 实践应用
- 理论如何应用于实践
- 实际案例分析
- 操作步骤说明

### 6. 课后思考
- 本节课的启发
- 延伸阅读建议
- 课后练习或作业

## 格式要求
- 适合打印或复习的格式
- 清晰的标题和子标题
- 使用表格整理对比信息
- 用代码块标注公式或代码
"""

prompt_5 = """
# 短视频内容分析 Prompt

请将提供的视频转录文本分析为适合短视频创作的文案素材。

## 输出要求

### 1. 内容亮点
- 视频中最吸引人的3-5个亮点
- 适合制作爆款的内容元素

### 2. 情感钩子
- 能够引起观众共鸣的点
- 激发好奇心或兴趣的元素
- 情感触动点

### 3. 标题灵感
- 3-5个可能的爆款标题
- 包含情绪词、数字、疑问等元素

### 4. 开头钩子
- 吸引观众注意力的开头语
- 前3秒的内容设计

### 5. 内容结构
- 适合短视频的分段方式
- 每个片段的要点和亮点

### 6. 互动元素
- 可以引导评论的问题
- 可以引导点赞或关注的提示
- 互动话题建议

### 7. 金句/名言
- 适合传播的精彩语句
- 可以制作文字图片的句子

### 8. 热点关联
- 与当前热点话题的联系
- 可以借势的流行元素

## 格式要求
- 适合短视频创作者使用的格式
- 突出可操作的建议
- 便于快速应用
"""

prompt_6 = """
# 视频综合总结 Prompt

请对提供的视频转录文本进行全面综合的总结。

## 输出要求

### 1. 内容概览
- 视频基本信息（主题、时长、类型）
- 主要内容简述
- 目标受众

### 2. 结构分析
- 视频的整体结构
- 各部分的主要内容
- 内容间的逻辑关系

### 3. 详细总结
- 按部分详细总结内容
- 保留重要细节
- 突出核心观点

### 4. 价值评估
- 视频的实用价值
- 内容质量评价
- 独特见解或创新点

### 5. 适用场景
- 适合哪些人群观看
- 在什么情况下有参考价值
- 应用建议

### 6. 相关推荐
- 类似主题的其他内容
- 延伸学习建议
- 补充材料推荐

## 格式要求
- 全面但不冗长
- 结构清晰，层次分明
- 保留重要细节
- 便于理解和分享
"""

prompt_templates = {
    "default课堂笔记": prompt_default,
    "youtube_英文笔记": prompt_1,
    "youtube_结构化提取": prompt_2,
    "youtube_精炼提取": prompt_3,
    "youtube_专业课笔记": prompt_4,
    "爆款短视频文案": prompt_5,
    "youtube_视频总结": prompt_6,
}
