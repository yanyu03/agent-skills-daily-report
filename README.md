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

## Cloudflare Pages 部署准备

`.github/workflows/cloudflare_pages.yml` 使用 Wrangler Direct Upload，将 `blog` 分支的 `docs/` 发布到 Cloudflare Pages 项目 `agent-skills-daily-report`，生产分支固定为 `blog`。发布不依赖自定义域名，Cloudflare 会提供默认的 `pages.dev` 地址。

首次发布前需要：

1. 在目标 Cloudflare 账户中创建一个具有 **Cloudflare Pages: Edit** 权限的 API Token。
2. 在 GitHub 仓库 `Settings → Secrets and variables → Actions` 中添加：
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
3. 从 `main` 分支手动运行“部署到 Cloudflare Pages”工作流。工作流会幂等地创建 Pages 项目、校验生产分支并发布站点，完成后以工作流输出的 `pages.dev` 地址为准。

也可以使用 GitHub CLI 设置 secrets：

```bash
gh secret set CLOUDFLARE_API_TOKEN --repo yanyu03/agent-skills-daily-report
gh secret set CLOUDFLARE_ACCOUNT_ID --repo yanyu03/agent-skills-daily-report --body "<Cloudflare Account ID>"
```

如需自定义域名，可在部署完成后从 Cloudflare Pages 项目中单独添加；它不是发布前置条件。
