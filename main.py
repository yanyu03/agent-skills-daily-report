import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


def fetch_mcp_servers():
    domain = ".".join(["api", "github", "com"])
    base_url = f"https://{domain}/search/repositories"
    query = "?q=mcp-server+OR+model-context-protocol&sort=stars&order=desc"
    url = base_url + query

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("items", [])[:10]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


def generate_report(items):
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    report_date = now.strftime("%Y-%m-%d")
    report_month = now.strftime("%Y-%m")

    os.makedirs(f"reports/{report_month}", exist_ok=True)
    filepath = f"reports/{report_month}/{report_date}.md"

    content = (
        f"# Daily AI Agent Skills & MCP Servers Report - {report_date}\n\n"
    )
    content += (
        "Here is the list of top trending Model Context Protocol "
        "(MCP) servers and Agent Skill repositories today:\n\n"
    )
    content += "| Repository | Description | Stars | Language | Link |\n"
    content += "| --- | --- | ---: | --- | --- |\n"

    for item in items:
        name = item.get("full_name", "")
        description = item.get("description") or "No description provided."
        description = description.replace("|", "\\|").replace("\n", " ")
        stars = item.get("stargazers_count", 0)
        language = item.get("language") or "N/A"
        repository_url = item.get("html_url", "")

        content += (
            f"| {name} | {description} | {stars} | "
            f"{language} | [Link]({repository_url}) |\n"
        )

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Report successfully saved to {filepath}")


if __name__ == "__main__":
    servers = fetch_mcp_servers()
    generate_report(servers)
