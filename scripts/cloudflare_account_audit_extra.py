from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CF_API = "https://api.cloudflare.com/client/v4"
GH_API = "https://api.github.com"
CF_TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
GH_TOKEN = os.environ["GITHUB_TOKEN"]
REPOSITORY = os.environ["GITHUB_REPOSITORY"]
OUTPUT = Path("audit/cloudflare-account-extra.md")


def get_json(url: str, headers: dict[str, str]) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(payload)
        except json.JSONDecodeError:
            return exc.code, {"message": payload[:500]}


def main() -> None:
    cf_headers = {
        "Authorization": f"Bearer {CF_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "agent-skills-daily-report-account-audit",
    }
    gh_headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "agent-skills-daily-report-account-audit",
    }

    lines = ["# Cloudflare 账号与部署链补充审计", ""]

    query = urllib.parse.urlencode({"account.id": ACCOUNT_ID, "per_page": 50})
    zone_status, zone_data = get_json(f"{CF_API}/zones?{query}", cf_headers)
    lines.extend(["## 当前 Token 可见的 Zone", ""])
    if zone_status == 200 and zone_data.get("success"):
        zones = zone_data.get("result") or []
        lines.append(f"- **可见 Zone 数量：** {len(zones)}")
        if zones:
            for zone in zones:
                lines.append(
                    f"- `{zone.get('name')}`：status=`{zone.get('status')}`，development_mode=`{zone.get('development_mode')}`"
                )
        else:
            lines.append("- 当前 API Token 在此 Account ID 下看不到任何 Zone。")
        lines.append(
            f"- **是否包含 `250221.xyz`：** {'是' if any(zone.get('name') == '250221.xyz' for zone in zones) else '否'}"
        )
    else:
        lines.append(f"- 无法列出 Zone：HTTP {zone_status}，响应 `{json.dumps(zone_data, ensure_ascii=False)[:500]}`")

    runs_status, runs_data = get_json(
        f"{GH_API}/repos/{REPOSITORY}/actions/workflows/cloudflare_pages.yml/runs?per_page=8",
        gh_headers,
    )
    lines.extend(["", "## Cloudflare Pages 工作流最近运行", ""])
    if runs_status == 200:
        runs = runs_data.get("workflow_runs") or []
        if not runs:
            lines.append("没有读取到运行记录。")
        for run in runs:
            lines.append(
                "- "
                f"`{run.get('id')}`：event=`{run.get('event')}`，branch=`{run.get('head_branch')}`，"
                f"status=`{run.get('status')}`，conclusion=`{run.get('conclusion')}`，"
                f"created=`{run.get('created_at')}`，updated=`{run.get('updated_at')}`"
            )

        if runs:
            latest = runs[0]
            jobs_status, jobs_data = get_json(
                f"{GH_API}/repos/{REPOSITORY}/actions/runs/{latest.get('id')}/jobs?per_page=100",
                gh_headers,
            )
            lines.extend(["", "### 最新运行任务", ""])
            if jobs_status == 200:
                for job in jobs_data.get("jobs") or []:
                    lines.append(
                        f"- **{job.get('name')}：** status=`{job.get('status')}`，conclusion=`{job.get('conclusion')}`"
                    )
                    failed_steps = [
                        step.get("name")
                        for step in (job.get("steps") or [])
                        if step.get("conclusion") == "failure"
                    ]
                    if failed_steps:
                        lines.append(f"  - 失败步骤：{', '.join(failed_steps)}")
            else:
                lines.append(f"无法读取最新运行 Jobs：HTTP {jobs_status}")
    else:
        lines.append(f"无法读取运行记录：HTTP {runs_status}，响应 `{json.dumps(runs_data, ensure_ascii=False)[:500]}`")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"补充审计报告已写入：{OUTPUT}")


if __name__ == "__main__":
    main()
