from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = "https://api.cloudflare.com/client/v4"
ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
API_TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
PROJECT = os.environ.get("CF_PAGES_PROJECT", "agent-skills-daily-report")
CUSTOM_DOMAIN = os.environ.get("CF_CUSTOM_DOMAIN", "skill.250221.xyz")
ZONE_NAME = os.environ.get("CF_ZONE_NAME", "250221.xyz")
BLOG_ROOT = Path(os.environ.get("BLOG_ROOT", "blog-site/docs"))
REPORT_PATH = Path(os.environ.get("REPORT_PATH", "audit/cloudflare-cache-report.md"))


def api_get(path: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "agent-skills-daily-report-cache-audit",
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
            return exc.code, {"success": False, "errors": [{"message": payload[:500]}]}


def public_get(url: str, *, no_cache: bool = False) -> dict[str, Any]:
    headers = {"User-Agent": "agent-skills-daily-report-cache-audit"}
    if no_cache:
        headers["Cache-Control"] = "no-cache"
        headers["Pragma"] = "no-cache"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            normalized_headers = {key.lower(): value for key, value in response.headers.items()}
            return {
                "ok": True,
                "status": response.status,
                "url": response.geturl(),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "headers": normalized_headers,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
            "headers": {key.lower(): value for key, value in exc.headers.items()},
        }
    except Exception as exc:  # noqa: BLE001 - audit must continue
        return {"ok": False, "status": 0, "url": url, "error": str(exc), "headers": {}}


def local_file(path: str) -> dict[str, Any]:
    file_path = BLOG_ROOT / path.lstrip("/")
    if not file_path.is_file():
        return {"exists": False, "path": str(file_path)}
    body = file_path.read_bytes()
    return {
        "exists": True,
        "path": str(file_path),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }


def api_error(data: dict[str, Any]) -> str:
    errors = data.get("errors") or []
    if not errors:
        return "未返回详细错误"
    return "；".join(str(item.get("message") or item.get("code") or item) for item in errors[:3])


def header_summary(result: dict[str, Any]) -> str:
    headers = result.get("headers") or {}
    fields = [
        ("CF-Cache-Status", headers.get("cf-cache-status", "-")),
        ("Age", headers.get("age", "-")),
        ("Cache-Control", headers.get("cache-control", "-")),
        ("CDN-Cache-Control", headers.get("cdn-cache-control", "-")),
        ("ETag", headers.get("etag", "-")),
        ("Last-Modified", headers.get("last-modified", "-")),
        ("CF-Ray", headers.get("cf-ray", "-")),
    ]
    return "<br>".join(f"**{name}:** `{value}`" for name, value in fields)


def compact(value: Any, limit: int = 220) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> None:
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    lines = [
        "# Cloudflare Pages 缓存审计",
        "",
        f"- **生成时间：** {generated_at}",
        f"- **Pages 项目：** `{PROJECT}`",
        f"- **自定义域名：** `{CUSTOM_DOMAIN}`",
        f"- **Zone：** `{ZONE_NAME}`",
        "- **安全说明：** 报告不输出 API Token 或完整 Account ID。",
        "",
    ]

    project_status, project_data = api_get(f"/accounts/{ACCOUNT_ID}/pages/projects/{PROJECT}")
    pages_base = f"https://{PROJECT}.pages.dev"
    latest_deployment: dict[str, Any] = {}
    if project_status == 200 and project_data.get("success"):
        project = project_data.get("result") or {}
        subdomain = project.get("subdomain") or f"{PROJECT}.pages.dev"
        pages_base = subdomain if str(subdomain).startswith("http") else f"https://{subdomain}"
        latest_deployment = project.get("latest_deployment") or {}
        lines.extend(
            [
                "## Pages 项目状态",
                "",
                f"- **API 状态：** 正常（HTTP {project_status}）",
                f"- **生产分支：** `{project.get('production_branch') or '未知'}`",
                f"- **pages.dev：** `{pages_base}`",
                f"- **绑定域名：** {', '.join(f'`{domain}`' for domain in (project.get('domains') or [])) or '未返回'}",
                f"- **最近部署 ID：** `{latest_deployment.get('id') or '未知'}`",
                f"- **最近部署环境：** `{latest_deployment.get('environment') or '未知'}`",
                f"- **最近部署时间：** `{latest_deployment.get('created_on') or latest_deployment.get('modified_on') or '未知'}`",
                f"- **最近部署地址：** `{latest_deployment.get('url') or '未知'}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Pages 项目状态",
                "",
                f"- **API 状态：** 读取失败（HTTP {project_status}）",
                f"- **错误：** {api_error(project_data)}",
                "",
            ]
        )

    zone_query = urllib.parse.urlencode(
        {"name": ZONE_NAME, "account.id": ACCOUNT_ID, "status": "active", "per_page": 5}
    )
    zone_status, zone_data = api_get(f"/zones?{zone_query}")
    zone_id = ""
    if zone_status == 200 and zone_data.get("success") and zone_data.get("result"):
        zone = zone_data["result"][0]
        zone_id = str(zone.get("id") or "")
        lines.extend(
            [
                "## Zone 与缓存设置",
                "",
                f"- **Zone 状态：** `{zone.get('status') or '未知'}`",
                f"- **开发模式：** `{zone.get('development_mode')}`",
            ]
        )

        for setting_name in ("cache_level", "browser_cache_ttl", "always_online"):
            status, data = api_get(f"/zones/{zone_id}/settings/{setting_name}")
            if status == 200 and data.get("success"):
                result = data.get("result") or {}
                lines.append(f"- **{setting_name}：** `{result.get('value')}`")
            else:
                lines.append(f"- **{setting_name}：** 无法读取（HTTP {status}，{api_error(data)}）")

        rules_status, rules_data = api_get(
            f"/zones/{zone_id}/rulesets/phases/http_request_cache_settings/entrypoint"
        )
        lines.extend(["", "### Cache Rules", ""])
        if rules_status == 200 and rules_data.get("success"):
            rules = (rules_data.get("result") or {}).get("rules") or []
            cache_rules = [rule for rule in rules if rule.get("action") == "set_cache_settings"]
            if cache_rules:
                for index, rule in enumerate(cache_rules, 1):
                    lines.extend(
                        [
                            f"#### {index}. {rule.get('description') or '未命名规则'}",
                            "",
                            f"- **启用：** `{rule.get('enabled', True)}`",
                            f"- **条件：** `{rule.get('expression') or '未返回'}`",
                            f"- **缓存参数：** `{compact(rule.get('action_parameters') or {})}`",
                            "",
                        ]
                    )
            else:
                lines.append("没有发现启用 `set_cache_settings` 的 Cache Rule。")
        elif rules_status == 404:
            lines.append("该阶段没有配置 Cache Rules。")
        else:
            lines.append(f"无法读取 Cache Rules（HTTP {rules_status}，{api_error(rules_data)}）。")

        pagerules_status, pagerules_data = api_get(
            f"/zones/{zone_id}/pagerules?status=active&per_page=100"
        )
        lines.extend(["", "### 旧版 Page Rules", ""])
        if pagerules_status == 200 and pagerules_data.get("success"):
            page_rules = pagerules_data.get("result") or []
            cache_page_rules = []
            for rule in page_rules:
                actions = rule.get("actions") or []
                if any(
                    action.get("id") in {"cache_level", "browser_cache_ttl", "edge_cache_ttl", "cache_key"}
                    for action in actions
                ):
                    cache_page_rules.append(rule)
            if cache_page_rules:
                for index, rule in enumerate(cache_page_rules, 1):
                    targets = rule.get("targets") or []
                    lines.append(
                        f"- **规则 {index}：** targets=`{compact(targets)}`；actions=`{compact(rule.get('actions') or [])}`"
                    )
            else:
                lines.append("没有发现会影响缓存的启用 Page Rule。")
        else:
            lines.append(
                f"无法读取 Page Rules（HTTP {pagerules_status}，{api_error(pagerules_data)}）。"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "## Zone 与缓存设置",
                "",
                f"无法读取 Zone（HTTP {zone_status}，{api_error(zone_data)}）。API Token 可能只有 Pages 权限，没有 Zone/Rulesets 读取权限。",
                "",
            ]
        )

    paths = ["/index.html", "/post/5.html", "/assets/skill-report.css"]
    nonce = str(int(time.time()))
    observations: list[dict[str, Any]] = []
    lines.extend(
        [
            "## 内容与响应头对照",
            "",
            "比较 `blog` 分支文件、pages.dev 和自定义域名。查询参数请求同时携带 `Cache-Control: no-cache`。",
            "",
            "| 文件 | 本地 | pages.dev | 自定义域名 | 自定义域名（绕缓存） |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for path in paths:
        local = local_file(path)
        pages = public_get(f"{pages_base}{path}?cf_audit={nonce}", no_cache=True)
        custom = public_get(f"https://{CUSTOM_DOMAIN}{path}")
        separator = "&" if "?" in path else "?"
        custom_bust = public_get(
            f"https://{CUSTOM_DOMAIN}{path}{separator}cf_audit={nonce}", no_cache=True
        )

        local_hash = local.get("sha256")
        pages_match = bool(local_hash and pages.get("sha256") == local_hash)
        custom_match = bool(local_hash and custom.get("sha256") == local_hash)
        bust_match = bool(local_hash and custom_bust.get("sha256") == local_hash)
        observations.append(
            {
                "path": path,
                "local": local,
                "pages": pages,
                "custom": custom,
                "custom_bust": custom_bust,
                "pages_match": pages_match,
                "custom_match": custom_match,
                "bust_match": bust_match,
            }
        )

        local_cell = (
            f"`{str(local_hash)[:12]}` / {local.get('bytes')} B"
            if local.get("exists")
            else "不存在"
        )
        pages_cell = f"HTTP {pages.get('status')}<br>匹配本地：**{'是' if pages_match else '否'}**"
        custom_cell = f"HTTP {custom.get('status')}<br>匹配本地：**{'是' if custom_match else '否'}**"
        bust_cell = f"HTTP {custom_bust.get('status')}<br>匹配本地：**{'是' if bust_match else '否'}**"
        lines.append(f"| `{path}` | {local_cell} | {pages_cell} | {custom_cell} | {bust_cell} |")

    lines.extend(["", "### 自定义域名响应头", ""])
    for item in observations:
        lines.extend(
            [
                f"#### `{item['path']}`",
                "",
                "**普通请求**",
                "",
                header_summary(item["custom"]),
                "",
                "**带查询参数与 no-cache 请求**",
                "",
                header_summary(item["custom_bust"]),
                "",
            ]
        )

    direct_current = all(item["pages_match"] for item in observations)
    custom_current = all(item["custom_match"] for item in observations)
    bust_current = all(item["bust_match"] for item in observations)

    if direct_current and custom_current:
        diagnosis = "未发现自定义域名缓存旧页面；pages.dev 和自定义域名均与 `blog` 分支一致。"
    elif direct_current and not custom_current and bust_current:
        diagnosis = "Pages 部署已经更新，但自定义域名普通请求仍返回旧内容；高度疑似边缘 Cache Rule/Page Rule 或浏览器缓存。"
    elif direct_current and not custom_current and not bust_current:
        diagnosis = "pages.dev 已更新，但自定义域名即使带随机查询参数仍不一致；优先检查自定义域名映射、忽略查询参数的缓存键规则或 Worker 路由。"
    elif not direct_current:
        diagnosis = "pages.dev 与 `blog` 分支尚不一致，问题更可能在 Pages 部署链或部署版本，而不是自定义域名缓存。"
    else:
        diagnosis = "结果不完全一致，需要结合逐文件哈希与响应头判断。"

    lines.extend(
        [
            "## 自动诊断",
            "",
            f"> {diagnosis}",
            "",
            "### 判断矩阵",
            "",
            f"- **pages.dev 全部匹配本地：** {'是' if direct_current else '否'}",
            f"- **自定义域名普通请求全部匹配：** {'是' if custom_current else '否'}",
            f"- **自定义域名绕缓存请求全部匹配：** {'是' if bust_current else '否'}",
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Cloudflare 缓存审计报告已写入：{REPORT_PATH}")


if __name__ == "__main__":
    main()
