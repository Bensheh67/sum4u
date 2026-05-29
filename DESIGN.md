# Design System — summary4u

## Product Context

- **What this is:** 音视频总结工具 (Video/Audio Summarizer) — 命令行 + Web 界面
- **Who it's for:** 学习者/知识工作者（学生、职场人）— 需要从视频/音频中快速提取精华
- **Space/industry:** 知识管理、学习工具、AI 生产力软件
- **Project type:** Web 工具类应用 (utility app with dashboard)

## Aesthetic Direction

- **Direction:** 学术极简 (Academic Minimal)
- **Decoration level:** 极低 — 靠排版和间距建立层次，不靠图形装饰
- **Mood:** 像 Notion 但专注于视频总结，专业但不冰冷，高信息密度但有呼吸感
- **Reference:** Notion, Notability, Obsidian — 知识工具的视觉语言

## Typography

- **Display/Hero:** Instrument Sans — 现代几何无衬线，有温度，不像 Inter 那么冷
  - Google Fonts: `Instrument+Sans:wght@400;500;600;700`
  - Fallback: -apple-system, BlinkMacSystemFont, sans-serif
- **Body:** Source Sans 3 — 极佳可读性，适合长文本内容
  - Google Fonts: `Source+Sans+3:wght@300;400;500;600`
  - Fallback: -apple-system, BlinkMacSystemFont, sans-serif
- **UI/Labels:** 同 Source Sans 3，weight 500-600
- **Data/Paths/Code:** JetBrains Mono — 等宽， tabular-nums 支持
  - Google Fonts: `JetBrains+Mono:wght@400;500`
- **Loading:** 系统字体栈保证首屏可读

### Type Scale

```
Display XL:  Instrument Sans 700, 48px, letter-spacing: -1px, line-height: 1.1
Display LG:   Instrument Sans 600, 32px, letter-spacing: -0.5px
Display MD:   Instrument Sans 600, 20px
Body LG:      Source Sans 3 400, 18px, line-height: 1.6
Body:         Source Sans 3 400, 14px, line-height: 1.6
Body Small:   Source Sans 3 400, 12px, color: text-secondary
Mono:         JetBrains Mono 400, 13px
```

## Color

- **Approach:** Restrained — 主色极少出现，重点在结构和服务
- **Primary:** `#0D9488` (teal) — 品牌色，用于 CTA、active 状态、重要标签
  - Hover: `#0F766E`
  - Light: `#CCFBF1` (用于选中背景)
- **Secondary:** `#14B8A6` — 辅助色，用于渐变、次要强调
- **Background:** `#FFFFFF`
- **Surface:** `#F8FAFC` — 卡片、侧边栏背景
- **Surface Hover:** `#F1F5F9`
- **Border:** `#E2E8F0`
- **Border Strong:** `#CBD5E1`
- **Text:** `#1E293B` — 主文字
- **Text Secondary:** `#64748B` — 次要文字
- **Text Muted:** `#94A3B8` — 辅助信息、时间戳等
- **Success:** `#10B981`
- **Warning:** `#F59E0B`
- **Error:** `#EF4444`
- **Info:** `#3B82F6`

### Dark Mode Strategy

深色模式下：
- Background: `#0F172A`
- Surface: `#1E293B`
- Surface Hover: `#334155`
- Border: `#334155`
- Text: `#F1F5F9`
- Text Secondary: `#94A3B8`
- Text Muted: `#64748B`

降低饱和度 10-20%，保持蓝绿主色调。

## Spacing

- **Base unit:** 8px
- **Density:** 舒适 (comfortable) — 学习场景需要适当留白降低认知疲劳
- **Scale:**
```
2xs: 2px   (icon gap)
xs:  4px   (tight gap)
sm:  8px   (element gap)
md:  16px  (section gap)
lg:  24px  (card padding)
xl:  32px  (section spacing)
2xl: 48px  (large spacing)
3xl: 64px  (page spacing)
```

## Layout

- **Approach:** Grid-disciplined — 严格列布局，可预测对齐
- **Grid columns:** 12-column grid, 24px gutter
- **Max content width:** 1200px
- **Sidebar width:** 240px (fixed)
- **Header height:** 56px
- **Border radius scale:**
  - sm: 4px (badges, small elements)
  - md: 8px (buttons, inputs, cards)
  - lg: 12px (modals, large cards)

### Responsive Breakpoints

```
Mobile:  < 768px  — 侧边栏隐藏，汉堡菜单触发
Tablet:  768px+   — 双栏布局
Desktop: 1024px+  — 完整三栏布局
Wide:    1280px+  — max-width 限制
```

## Motion

- **Approach:** 最小功能型 (minimal-functional) — 仅必要的过渡，不喧宾夺主
- **Easing:**
  - Enter: ease-out
  - Exit: ease-in
  - Move: ease-in-out
- **Duration:**
  - Micro: 50-100ms (hover states, toggles)
  - Short: 150-250ms (buttons, inputs)
  - Medium: 250-400ms (cards, panels)
  - Long: 400-700ms (modals, drawers)
- **No decorative animation** — 所有动效服务于功能反馈

## Component Tokens

### Buttons

```
Primary:   bg: primary,    text: white,     border: none
Secondary: bg: surface,    text: text,      border: border
Ghost:     bg: transparent,text: secondary, border: none
```

- Height: 40px (标准), 36px (header buttons)
- Padding: 0 16px
- Font: Source Sans 3 500, 14px
- Border-radius: md (8px)

### Inputs

- Height: 40px
- Padding: 0 12px
- Border: 1px solid border
- Focus: border-color: primary, box-shadow: 0 0 0 3px rgba(13,148,136,0.1)
- Border-radius: md (8px)

### Cards

- Background: white (bg)
- Border: 1px solid border
- Border-radius: lg (12px)
- Padding: 24px (lg), 16px (md), 12px (sm)
- Shadow: 0 1px 2px rgba(0,0,0,0.04) (sm)

### Navigation

- Nav item height: 36px
- Padding: 9px 12px
- Border-radius: md (8px)
- Active: bg: primary-light, color: primary
- Hover: bg: surface-hover, color: text

## Decisions Log

| Date       | Decision                      | Rationale |
|------------|-------------------------------|-----------|
| 2026-05-29 | Initial design system created | Created by /design-consultation — academic minimal direction |
| 2026-05-29 | Blue-green primary (#0D9488) | Breaks AI tool purple-blue cliché; connotes knowledge/growth |
| 2026-05-29 | Instrument Sans + Source Sans 3 | Warm geometric sans vs cold defaults (Inter/Roboto) |
| 2026-05-29 | Dark mode with saturation reduction | Maintains teal brand while reducing eye strain |