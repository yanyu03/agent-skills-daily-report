# AI Agent Skills 中文观察

这是一个自动化的中文 AI Agent、Agent Skills 与 MCP Server 项目观察站。仓库每天从 GitHub Search API 获取高关注度项目，生成中文结构化日报，并通过 Gmeek 发布为 GitHub Pages 博客。

## 在线站点

- 博客地址：<https://yanyu03.github.io/agent-skills-daily-report/>
- 历史 Markdown：[`reports/`](../reports/)
- 博客文章源：仓库的 Issues，标签为 `每日简报`

## 自动发布流程

每天北京时间 00:00，工作流会依次完成：

1. 获取 Agent Skills、MCP Server 和相关智能体工具项目。
2. 生成中文 Markdown 日报并保存到 `reports/YYYY-MM/`。
3. 创建或更新当天的 `每日简报` Issue。
4. 触发 Gmeek，将 Issue 渲染为静态博客文章。
5. 将站点部署到 GitHub Pages。

## 报告说明

报告按照 GitHub Search API 返回的 Star 数排序，用于观察长期高关注度项目，不等同于 GitHub 官方趋势榜。项目简介保留仓库原文，避免自动翻译改变技术含义。

## 手动运行

- `Actions → 生成并发布中文日报 → Run workflow`：重新生成当天日报并发布文章。
- `Actions → 构建并部署 Gmeek 中文博客 → Run workflow`：重新生成整个博客站点。

## 首次启用 GitHub Pages

进入仓库：

`Settings → Pages → Build and deployment → Source → GitHub Actions`

完成这一项后，Gmeek 工作流即可部署站点。

## 主要文件

- `main.py`：采集数据并生成中文日报。
- `publish_issue.py`：将日报同步为 Gmeek 使用的 Issue。
- `config.json`：Gmeek 中文站点配置。
- `.github/workflows/daily_report.yml`：日报发布工作流。
- `.github/workflows/Gmeek.yml`：博客构建和 Pages 部署工作流。

站点框架基于 [Gmeek](https://github.com/Meekdai/Gmeek)。
