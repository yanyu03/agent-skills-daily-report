# AI Agent Skills 中文观察｜Python 源码分支

本分支只保存日报采集、分析和发布所需的 Python 源码、配置、测试与 Markdown 报告。

## 分支职责

- `py`：Python 源码、配置、测试和 `reports/`。
- `blog`：Gmeek 生成的静态站点、备份和 `blogBase.json`。
- `main`：GitHub Actions 调度与分支编排。

线上站点：<https://skill.250221.xyz/>

主要入口：

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py
python publish_issue.py
```
