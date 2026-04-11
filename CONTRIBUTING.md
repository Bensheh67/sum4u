# 贡献指南 (Contributing Guidelines)

感谢你对本项目的关注！欢迎通过提交 Issue 和 Pull Request 来改进这个项目。

## 📋 目录

- [代码行为准则](#代码行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [提交规范](#提交规范)
- [Pull Request 指南](#pull-request-指南)
- [Issue 指南](#issue-指南)
- [安全注意事项](#安全注意事项)

## 代码行为准则

本项目采纳 [Contributor Covenant](https://www.contributor-covenant.org/) 的行为准则。请尊重所有贡献者和用户，营造一个开放和友好的社区环境。

## 如何贡献

### 1. Fork 项目

在 GitHub 上点击 Fork 按钮创建你自己的分支。

### 2. 克隆你的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/summary4u.git
cd summary4u
```

### 3. 创建新分支

```bash
git checkout -b feature/your-feature-name
# 或者
git checkout -b fix/your-bug-fix
```

分支命名规范：
- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构
- `test/xxx` - 测试相关

### 4. 进行更改

进行你的更改，确保代码符合以下要求：
- 遵循现有的代码风格
- 添加必要的注释
- 更新相关文档

### 5. 测试你的更改

```bash
# 运行基本测试
make test

# 或者手动测试
python -m pytest tests/
```

### 6. 提交更改

遵循 [提交规范](#提交规范)。

### 7. 推送到你的 Fork

```bash
git push origin feature/your-feature-name
```

### 8. 创建 Pull Request

在 GitHub 上导航到你的 Fork，点击 "New Pull Request" 按钮。

## 提交规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

### 示例

```
feat(youtube): 添加 YouTube 视频下载功能

- 使用 yt-dlp 下载 YouTube 视频
- 支持多种格式选择
- 自动提取音频

Closes #123
```

```
fix(audio): 修复大文件转录失败问题

当音频文件大于 100MB 时，现在会自动分段处理。

Fixes #456
```

## Pull Request 指南

### PR 标题

使用清晰的标题，遵循 `<type>: <description>` 格式。

### PR 描述模板

```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 重构
- [ ] 其他（请说明）

## 描述
简要描述你的更改内容和原因。

## 相关 Issue
Closes #ISSUE_NUMBER

## 测试
描述你如何测试这些更改。

## 检查清单
- [ ] 代码遵循项目风格指南
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 通过了所有测试
- [ ] 没有提交敏感信息（API 密钥等）
```

## Issue 指南

### 提交 Issue 前

1. 搜索现有的 Issue，看看是否已经有人报告了相同的问题
2. 确保使用的是最新版本的代码

### Bug Report 模板

```markdown
**描述问题**
简要描述问题是什么。

**复现步骤**
1. ...
2. ...
3. ...

**期望行为**
描述你期望发生什么。

**实际行为**
描述实际发生了什么。

**环境信息**
- OS: [e.g. macOS 14.0]
- Python 版本：[e.g. 3.11]
- 相关依赖版本：[e.g. yt-dlp 2024.x.x]

**截图**
如果适用，添加截图。

**其他信息**
任何其他你想提供的信息。
```

### Feature Request 模板

```markdown
**功能描述**
简要描述你想要的功能。

**使用场景**
描述这个功能能解决什么问题。

**实现建议**
如果你有实现思路，请分享。

**其他信息**
任何其他你想提供的信息。
```

## 安全注意事项

### ⚠️ 重要：保护 API 密钥

在贡献代码时，请特别注意：

1. **绝不要提交包含真实 API 密钥的文件**
   - `config.json` - 已添加到 `.gitignore`
   - `.env` - 已添加到 `.gitignore`
   - 任何包含 `api_key`, `secret`, `token`, `password` 的文件

2. **在提交前检查**
   ```bash
   # 检查是否有敏感文件
   git status
   
   # 检查提交历史是否包含 API 密钥
   git log -p --all | grep -i "sk-"
   ```

3. **使用示例配置文件**
   - 在 `config_example.json` 中使用占位符
   - 例如：`"api_key": "YOUR_API_KEY_HERE"`

4. **如果意外提交了敏感信息**
   - 立即删除敏感文件
   - 使用 `git filter-branch` 或 BFG Repo-Cleaner 从历史中移除
   - 轮换（撤销并重新生成）所有受影响的 API 密钥

## 代码风格

- 遵循 PEP 8 风格指南
- 使用 4 个空格缩进
- 函数和变量使用 snake_case 命名
- 类使用 PascalCase 命名
- 保持函数简洁，单一职责

## 文档

- 为新功能添加文档
- 更新 README.md 中的相关说明
- 在代码中添加清晰的注释

## 问题？

如果你有任何问题，欢迎在 Issue 中提问，或者加入我们的讨论。

感谢你的贡献！ 🎉
