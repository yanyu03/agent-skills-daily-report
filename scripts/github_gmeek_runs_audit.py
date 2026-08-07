from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
REPOSITORY = os.environ["GITHUB_REPOSITORY"]
OUTPUT = Path("audit/gmeek-workflow-runs.md")


def get_json(url: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "agent-skills-daily-report-gmeek-audit",
        },
    )
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
    status, data = get_json(
        f"{API}/repos/{REPOSITORY}/actions/workflows/Gmeek.yml/runs?per_page=10"
    )
    lines = ["# Gmeek 上游工作流审计", ""]
    if status != 200:
        lines.append(f"无法读取 Gmeek 工作流：HTTP {status}，`{json.dumps(data, ensure_ascii=False)[:500]}`")
    else:
        runs = data.get("workflow_runs") or []
        for run in runs:
            lines.append(
                "- "
                f"`{run.get('id')}`：event=`{run.get('event')}`，branch=`{run.get('head_branch')}`，"
                f"status=`{run.get('status')}`，conclusion=`{run.get('conclusion')}`，"
                f"created=`{run.get('created_at')}`，updated=`{run.get('updated_at')}`"
            )

        for run in runs[:3]:
            run_id = run.get("id")
            job_status, job_data = get_json(
                f"{API}/repos/{REPOSITORY}/actions/runs/{run_id}/jobs?per_page=100"
            )
            lines.extend(["", f"## Run `{run_id}` Jobs", ""])
            if job_status != 200:
                lines.append(f"无法读取 Jobs：HTTP {job_status}")
                continue
            for job in job_data.get("jobs") or []:
                lines.append(
                    f"- **{job.get('name')}：** status=`{job.get('status')}`，conclusion=`{job.get('conclusion')}`"
                )
                for step in job.get("steps") or []:
                    if step.get("conclusion") in {"failure", "cancelled"}:
                        lines.append(
                            f"  - `{step.get('name')}`：conclusion=`{step.get('conclusion')}`"
                        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Gmeek 工作流审计已写入：{OUTPUT}")


if __name__ == "__main__":
    main()
