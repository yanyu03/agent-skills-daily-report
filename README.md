# AI Agent Skills 中文观察｜自动化调度分支

本仓库按职责拆分为三个分支：

| 分支 | 职责 |
| --- | --- |
| `main` | GitHub Actions 调度与部署编排 |
| `py` | Python 源码、配置、测试和 Markdown 日报 |
| `blog` | Gmeek 生成的静态站点与构建缓存 |

## 数据流

```text
main 定时调度
  → 检出 py，生成日报并更新 Issue
  → 从 py 读取 Gmeek 配置和文章数据
  → 将静态产物提交到 blog
  → 从 blog 部署 GitHub Pages 与 Cloudflare Pages
```

线上站点：<https://skill.250221.xyz/>

源码请切换到 [`py`](../../tree/py)，静态站点产物请切换到 [`blog`](../../tree/blog)。
