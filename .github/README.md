# AI Agent Skills 中文观察

这是一个自动化的中文 AI Agent、Agent Skills 与 MCP Server 项目观察站。仓库每天从 GitHub Search API 获取高关注度项目，生成带用途分类、适用场景、小白建议和开发者建议的中文日报，并通过 Gmeek 构建静态博客。

## 在线站点

- 主站：<https://skill.250221.xyz/>
- Cloudflare Pages 项目：`agent-skills-daily-report`
- GitHub Pages 备用地址：<https://yanyu03.github.io/agent-skills-daily-report/>
- 历史 Markdown：[`reports/`](../reports/)
- 博客文章源：仓库的 Issues，标签为 `每日简报`

## 自动发布流程

每天北京时间 00:00，工作流会依次完成：

1. 获取 Agent Skills、MCP Server 和相关智能体工具项目。
2. 根据名称、简介、Topics 和公开元数据判断主要用途与上手门槛。
3. 生成面向小白和开发者的场景化中文日报，保存到 `reports/YYYY-MM/`。
4. 创建或更新当天的 `每日简报` Issue。
5. 触发 Gmeek，将 Issue 渲染为静态博客文章。
6. 部署 GitHub Pages 备用站点。
7. Gmeek 工作流成功后，自动将 `docs/` 发布到 Cloudflare Pages，并绑定 `skill.250221.xyz`。

## Cloudflare Pages 凭据

Cloudflare 自动部署使用 GitHub Actions Secrets：

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

API Token 至少需要账户级 `Cloudflare Pages: Edit` 权限。工作流会使用官方 `cloudflare/wrangler-action` 部署，并通过 Pages API 幂等绑定自定义域名。

## 报告说明

报告按照 GitHub Search API 返回的 Star 数排序，用于观察长期高关注度项目，不等同于 GitHub 官方趋势榜。用途分类与人群建议用于初筛，正式选型仍需检查 README、许可证、维护状态、安全边界和实际部署成本。

## 手动运行

- `Actions → 生成并发布中文日报 → Run workflow`：重新生成当天日报并发布文章。
- `Actions → 构建并部署 Gmeek 中文博客 → Run workflow`：重新生成静态博客。
- `Actions → 部署到 Cloudflare Pages → Run workflow`：将最新 `docs/` 部署到 Cloudflare 并检查域名绑定。

## 主要文件

- `main.py`：采集数据、用途分类并生成场景化中文日报。
- `publish_issue.py`：将日报同步为 Gmeek 使用的 Issue。
- `config.json`：Gmeek 中文站点与主域名配置。
- `.github/workflows/daily_report.yml`：日报发布工作流。
- `.github/workflows/Gmeek.yml`：博客构建和 GitHub Pages 备用部署工作流。
- `.github/workflows/cloudflare_pages.yml`：Cloudflare Pages 与自定义域名部署工作流。

站点框架基于 [Gmeek](https://github.com/Meekdai/Gmeek)。
