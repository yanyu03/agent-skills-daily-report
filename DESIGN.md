# AI Agent Skills 中文观察 — DESIGN.md

## 设计目标

这是面向技术读者的长篇日报，不做营销落地页。视觉优先级依次为：

1. 长文阅读舒适；
2. Skill 推荐可快速扫描；
3. 表格和仓库目录在移动端可用；
4. 明暗主题保持一致；
5. 不覆盖 Gmeek/Primer 的导航与基础交互。

## 设计语言

- 阅读层：暖白/冷灰画布、白色文章面板、16px 正文字号、宽松行距。
- 信息层：低饱和紫色表示重点推荐，青色表示场景与辅助信息。
- 卡片层：细边框、14px 圆角、低强度阴影，不使用强烈渐变或霓虹。
- 数据层：概览指标使用响应式网格；表格保留完整信息并允许横向滚动。
- 交互层：折叠目录使用原生 details/summary，保持无 JavaScript 可用。

## 作用域

- Primer 继续负责 Header、按钮、标签与 Gmeek 基础组件。
- Tailwind Typography 只作用于 `#postBody.skill-report`。
- 自定义样式只作用于 `.skill-site`、`.skill-report`、`.skill-card` 等语义类。
- 禁用 Tailwind Preflight，避免重置 Primer。

## 设计令牌

- Accent: `#5b5bd6`
- Cyan: `#087e8b`
- Light canvas: `#f5f7fb`
- Light surface: `#ffffff`
- Dark canvas: `#0d1117`
- Dark surface: `#161b22`
- Radius: 8 / 14 / 20px
- Article maximum width: 1120px
- Home maximum width: 1180px

## 响应式规则

- 860px 以下：推荐卡片信息列由两列变一列，指标由四列变两列。
- 600px 以下：指标变单列，正文缩小内边距，表格横向滚动。
- 不隐藏正文信息，只调整布局。
