import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

TIMEZONE = ZoneInfo("Asia/Shanghai")
LABEL_NAME = "每日简报"
LABEL_COLOR = "0969DA"
LABEL_DESCRIPTION = "由自动化生成的 AI Agent Skills 与 MCP 中文日报"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少必要环境变量：{name}")
    return value


def api_request(
    session: requests.Session,
    method: str,
    url: str,
    **kwargs,
) -> requests.Response:
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(
            f"GitHub API 请求失败：{method} {url} -> "
            f"{response.status_code} {response.text[:500]}"
        )
    return response


def ensure_label(session: requests.Session, api_base: str) -> None:
    label_url = f"{api_base}/labels/{quote(LABEL_NAME, safe='')}"
    response = session.get(label_url, timeout=30)
    if response.status_code == 200:
        label = response.json()
        if (
            label.get("color", "").upper() != LABEL_COLOR
            or label.get("description") != LABEL_DESCRIPTION
        ):
            api_request(
                session,
                "PATCH",
                label_url,
                json={
                    "name": LABEL_NAME,
                    "color": LABEL_COLOR,
                    "description": LABEL_DESCRIPTION,
                },
            )
            print(f"已更新标签样式：{LABEL_NAME}")
        return
    if response.status_code != 404:
        raise RuntimeError(
            f"检查标签失败：{response.status_code} {response.text[:500]}"
        )

    api_request(
        session,
        "POST",
        f"{api_base}/labels",
        json={
            "name": LABEL_NAME,
            "color": LABEL_COLOR,
            "description": LABEL_DESCRIPTION,
        },
    )
    print(f"已创建标签：{LABEL_NAME}")


def find_existing_issue(
    session: requests.Session,
    api_base: str,
    title: str,
) -> dict | None:
    page = 1
    while page <= 5:
        response = api_request(
            session,
            "GET",
            f"{api_base}/issues",
            params={
                "state": "all",
                "labels": LABEL_NAME,
                "per_page": 100,
                "page": page,
            },
        )
        issues = response.json()
        for issue in issues:
            if "pull_request" not in issue and issue.get("title") == title:
                return issue
        if len(issues) < 100:
            break
        page += 1
    return None


def write_github_output(issue_number: int, issue_url: str) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"issue_number={issue_number}\n")
        output.write(f"issue_url={issue_url}\n")


def publish_daily_issue() -> None:
    token = require_env("GITHUB_TOKEN")
    repository = require_env("GITHUB_REPOSITORY")
    now = datetime.now(TIMEZONE)
    report_date = now.strftime("%Y-%m-%d")
    report_path = Path("reports") / now.strftime("%Y-%m") / f"{report_date}.md"
    if not report_path.exists():
        raise FileNotFoundError(f"找不到当日报告：{report_path}")

    title = f"AI Agent Skills 与 MCP 每日观察｜{report_date}"
    body = report_path.read_text(encoding="utf-8").strip()
    body += (
        "\n\n---\n\n"
        "> 本文由仓库自动化生成，并交由 Gmeek 构建为中文静态博客。\n"
    )

    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-skills-daily-report",
        }
    )
    api_base = f"https://api.github.com/repos/{repository}"

    ensure_label(session, api_base)
    existing = find_existing_issue(session, api_base, title)

    if existing:
        issue_number = int(existing["number"])
        issue_url = existing["html_url"]
        if (
            existing.get("body", "").strip() == body.strip()
            and existing.get("state") == "open"
        ):
            print(f"日报 Issue 已是最新：{issue_url}")
        else:
            response = api_request(
                session,
                "PATCH",
                f"{api_base}/issues/{issue_number}",
                json={"body": body, "state": "open", "labels": [LABEL_NAME]},
            )
            issue_url = response.json()["html_url"]
            print(f"已更新日报 Issue：{issue_url}")
    else:
        response = api_request(
            session,
            "POST",
            f"{api_base}/issues",
            json={"title": title, "body": body, "labels": [LABEL_NAME]},
        )
        created = response.json()
        issue_number = int(created["number"])
        issue_url = created["html_url"]
        print(f"已创建日报 Issue：{issue_url}")

    write_github_output(issue_number, issue_url)


if __name__ == "__main__":
    publish_daily_issue()
