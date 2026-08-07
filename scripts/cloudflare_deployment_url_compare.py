from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
PROJECT = os.environ.get("CF_PAGES_PROJECT", "agent-skills-daily-report")
BLOG_ROOT = Path("blog-site/docs")
OUTPUT = Path("audit/cloudflare-deployment-url-compare.md")


def get_json(url: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "agent-skills-daily-report-deployment-compare",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8", errors="replace"))


def fetch(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "agent-skills-daily-report-deployment-compare",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return {
                "status": response.status,
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "cache": response.headers.get("CF-Cache-Status", "-"),
                "age": response.headers.get("Age", "-"),
                "cache_control": response.headers.get("Cache-Control", "-"),
                "content_type": response.headers.get("Content-Type", "-"),
            }
    except Exception as exc:  # noqa: BLE001
        return {"status": 0, "error": str(exc), "sha256": "", "bytes": 0}


def main() -> None:
    status, data = get_json(f"{API_ROOT}/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}")
    lines = ["# Pages 唯一部署地址与生产别名对照", ""]
    if status != 200 or not data.get("success"):
        lines.append(f"无法读取 Pages 项目：HTTP {status}")
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    project = data.get("result") or {}
    deployment = project.get("latest_deployment") or {}
    immutable_base = str(deployment.get("url") or "").rstrip("/")
    subdomain = str(project.get("subdomain") or f"{PROJECT}.pages.dev")
    alias_base = (subdomain if subdomain.startswith("http") else f"https://{subdomain}").rstrip("/")
    lines.extend(
        [
            f"- **唯一部署地址：** `{immutable_base}`",
            f"- **生产别名：** `{alias_base}`",
            f"- **部署时间：** `{deployment.get('created_on') or '未知'}`",
            "",
            "| 文件 | 本地 SHA | 唯一部署匹配 | 生产别名匹配 | 唯一部署缓存 | 生产别名缓存 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )

    for path in ("/index.html", "/post/5.html", "/assets/skill-report.css"):
        local_body = (BLOG_ROOT / path.lstrip("/")).read_bytes()
        local_hash = hashlib.sha256(local_body).hexdigest()
        immutable = fetch(f"{immutable_base}{path}?audit=immutable")
        alias = fetch(f"{alias_base}{path}?audit=alias")
        immutable_match = immutable.get("sha256") == local_hash
        alias_match = alias.get("sha256") == local_hash
        immutable_cache = (
            f"CF={immutable.get('cache','-')} / Age={immutable.get('age','-')} / {immutable.get('cache_control','-')}"
        )
        alias_cache = f"CF={alias.get('cache','-')} / Age={alias.get('age','-')} / {alias.get('cache_control','-')}"
        lines.append(
            f"| `{path}` | `{local_hash[:12]}` | **{'是' if immutable_match else '否'}** "
            f"| **{'是' if alias_match else '否'}** | `{immutable_cache}` | `{alias_cache}` |"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"部署地址对照已写入：{OUTPUT}")


if __name__ == "__main__":
    main()
