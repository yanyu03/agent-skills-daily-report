# AI Agent Skills 中文观察｜Python 源码分支

本分支保存日报采集、Skill 结构分析、报告生成、发布脚本、测试与 Markdown 报告。

## 分支职责

- `py`：Python 源码、配置、测试和 `reports/`。
- `blog`：Gmeek 生成的静态站点、备份和 `blogBase.json`。
- `main`：GitHub Actions 调度与分支编排。

线上站点：<https://skill.250221.xyz/>

## 报告流程

1. 使用 GitHub Search API 获取高关注 Agent Skills、MCP 与相关仓库。
2. 对仓库做用途、许可证和代码活跃度初筛。
3. 在公开文件树中发现 `SKILL.md`，每个仓库最多读取 3 个，全期最多读取 20 个。
4. 提取 Skill 的 `name`、`description`、兼容性、预授权工具和配套资源。
5. 输出今日推荐 Skill、按场景浏览、仓库—Skill 目录和仓库层选型提醒。

Skill 的结构完整度和风险等级均为静态规则结果，不代表已经运行、审计或验证实际效果。

## 主要入口

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py
python publish_issue.py
```

核心文件：

- `main.py`：仓库分析与 Markdown 报告编排。
- `skill_analysis.py`：Skill 发现、frontmatter 解析、场景分类、结构评分和静态风险提示。
- `publish_issue.py`：将当日报告同步到 Gmeek 使用的 Issue。
