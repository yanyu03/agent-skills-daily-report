import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

TIMEZONE = ZoneInfo("Asia/Shanghai")
SEARCH_ENDPOINT = "https://api.github.com/search/repositories"
SEARCH_QUERY = "mcp-server OR model-context-protocol OR agent-skills"
REPORT_LIMIT = 10


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agent-skills-daily-report",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_projects() -> list[dict]:
    params = {
        "q": SEARCH_QUERY,
        "sort": "stars",
        "order": "desc",
        "per_page": REPORT_LIMIT,
    }

    try:
        response = requests.get(
            SEARCH_ENDPOINT,
            headers=github_headers(),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"GitHub 项目数据获取失败：{exc}") from exc

    items = response.json().get("items", [])
    if not items:
        raise RuntimeError("GitHub Search API 未返回任何项目，已停止生成空报告。")
    return items[:REPORT_LIMIT]


def clean_markdown_text(value: str | None) -> str:
    text = value or "暂无项目简介。"
    return " ".join(text.replace("|", "\\|").split())


def format_updated_at(value: str | None) -> str:
    if not value:
        return "未知"
    try:
        updated_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return updated_at.astimezone(TIMEZONE).strftime("%Y-%m-%d")
    except ValueError:
        return value[:10]


def language_summary(items: list[dict]) -> str:
    counts = Counter((item.get("language") or "未标注") for item in items)
    return "、".join(
        f"{language}（{count}）" for language, count in counts.most_common(4)
    )


def generate_report(items: list[dict]) -> Path:
    now = datetime.now(TIMEZONE)
    report_date = now.strftime("%Y-%m-%d")
    report_month = now.strftime("%Y-%m")
    generated_at = now.strftime("%Y-%m-%d %H:%M")

    output_dir = Path("reports") / report_month
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{report_date}.md"

    total_stars = sum(int(item.get("stargazers_count", 0)) for item in items)
    content = [
        f"# AI Agent Skills 与 MCP 每日观察｜{report_date}",
        "",
        "> [!NOTE]",
        "> 本报告由 GitHub Actions 自动生成，按 GitHub Search API 返回的 Star 数排序，用于观察高关注度项目；它不是 GitHub 官方趋势榜。",
        "",
        "## 今日概览",
        "",
        f"- **收录项目：** {len(items)} 个",
        f"- **合计 Stars：** {total_stars:,}",
        f"- **主要语言：** {language_summary(items)}",
        f"- **生成时间：** {generated_at}（Asia/Shanghai）",
        "",
        "## 项目榜单",
        "",
        "| 排名 | 项目 | 项目简介（原文） | Stars | 语言 | 最近更新 |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ]

    for rank, item in enumerate(items, start=1):
        name = item.get("full_name", "未知项目")
        repository_url = item.get("html_url", "")
        description = clean_markdown_text(item.get("description"))
        stars = int(item.get("stargazers_count", 0))
        language = item.get("language") or "未标注"
        updated_at = format_updated_at(item.get("updated_at"))
        content.append(
            f"| {rank} | [{name}]({repository_url}) | {description} | "
            f"{stars:,} | {language} | {updated_at} |"
        )

    content.extend(
        [
            "",
            "## 阅读提示",
            "",
            "- Star 数反映长期关注度，不代表项目当天新增热度。",
            "- 项目简介保留仓库原文，避免自动翻译造成技术含义偏差。",
            "- 选型时仍需继续检查许可证、最近提交、Issue 活跃度和实际部署成本。",
            "",
            "---",
            "",
            "由 `agent-skills-daily-report` 自动采集、整理并发布。",
            "",
        ]
    )

    filepath.write_text("\n".join(content), encoding="utf-8")
    print(f"中文报告已保存：{filepath}")
    return filepath


if __name__ == "__main__":
    generate_report(fetch_projects())
