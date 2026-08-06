from __future__ import annotations

import re
from collections import defaultdict
from pathlib import PurePosixPath
from urllib.parse import quote

import requests

GITHUB_API_ROOT = "https://api.github.com"
MAX_SKILLS_PER_REPOSITORY = 3
MAX_TOTAL_SKILLS = 20
MAX_SKILL_BYTES = 200_000

IGNORED_PATH_PARTS = {
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "vendor",
    "fixtures",
    "testdata",
}

PREFERRED_SKILL_ROOTS = (
    "skills/",
    ".agents/skills/",
    ".claude/skills/",
    ".github/skills/",
)

SCENARIO_RULES = (
    (
        "编程与代码审查",
        (
            "code review",
            "pull request",
            "debug",
            "diagnos",
            "refactor",
            "test-driven",
            "tdd",
            "git",
            "merge conflict",
            "codebase",
            "software engineering",
        ),
    ),
    (
        "内容与设计",
        (
            "design",
            "brand",
            "image",
            "video",
            "copywriting",
            "social post",
            "presentation",
            "slide",
            "creative",
            "visual",
        ),
    ),
    (
        "文档与办公",
        (
            "pdf",
            "docx",
            "xlsx",
            "spreadsheet",
            "document",
            "word",
            "powerpoint",
            "office",
        ),
    ),
    (
        "数据与研究",
        (
            "data analysis",
            "research",
            "dataset",
            "rag",
            "knowledge base",
            "retrieval",
            "statistics",
            "benchmark",
            "evaluation",
        ),
    ),
    (
        "Agent 构建",
        (
            "skill creator",
            "create new skills",
            "agent skill",
            "mcp server",
            "model context protocol",
            "agent framework",
            "prompt engineering",
            "triggering accuracy",
        ),
    ),
    (
        "自动化与运维",
        (
            "deploy",
            "cloudflare",
            "ci/cd",
            "github actions",
            "workflow automation",
            "monitor",
            "infrastructure",
            "operations",
            "release",
        ),
    ),
    (
        "方法论与协作",
        (
            "brainstorm",
            "planning",
            "requirements",
            "interview",
            "communication",
            "decision",
            "facilitat",
            "domain model",
            "architecture",
        ),
    ),
)

SCENARIO_DESCRIPTIONS = {
    "编程与代码审查": "调试、测试、重构、代码审查和版本控制工作流。",
    "内容与设计": "图文、品牌、视觉、演示和内容生产。",
    "文档与办公": "PDF、Word、表格、幻灯片和办公文件处理。",
    "数据与研究": "数据分析、检索、评测、知识库和研究任务。",
    "Agent 构建": "创建 Skill、MCP、Agent、提示词和评测流程。",
    "自动化与运维": "部署、监控、CI、云平台和自动化工作流。",
    "方法论与协作": "需求澄清、规划、架构、沟通和团队协作。",
    "其他场景": "公开元数据不足，需要阅读 Skill 正文后进一步判断。",
}

HIGH_RISK_PATTERNS = (
    ("涉及部署或发布", ("deploy", "publish to", "production environment", "release to")),
    ("涉及凭据或密钥", ("credential", "api key", "secret", "ssh key", "access token")),
    ("涉及删除或破坏性操作", ("delete files", "remove files", "rm -rf", "drop database")),
    ("涉及远程写入", ("git push", "send email", "create issue", "update database")),
)

MEDIUM_RISK_PATTERNS = (
    ("会执行命令或脚本", ("run command", "execute", "shell", "terminal", "subprocess")),
    ("会修改本地内容", ("write files", "edit files", "modify files", "update files")),
    ("可能访问网络或 API", ("external api", "http request", "network", "curl", "webhook")),
)


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").split())


def trim_text(value: str | None, limit: int = 220) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 1)].rstrip() + "…"


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse scalar and folded frontmatter without evaluating arbitrary YAML."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return {}, text

    frontmatter_lines = lines[1:closing_index]
    metadata: dict[str, str] = {}
    index = 0

    while index < len(frontmatter_lines):
        line = frontmatter_lines[index]
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            index += 1
            continue

        key, raw_value = match.groups()
        if raw_value in {"|", ">"}:
            block_lines: list[str] = []
            index += 1
            while index < len(frontmatter_lines):
                candidate = frontmatter_lines[index]
                if re.match(r"^[A-Za-z0-9_-]+:\s*", candidate):
                    break
                block_lines.append(candidate.strip())
                index += 1
            separator = "\n" if raw_value == "|" else " "
            metadata[key] = normalize_text(separator.join(block_lines))
            continue

        metadata[key] = unquote_yaml_scalar(raw_value)
        index += 1

    body = "\n".join(lines[closing_index + 1 :]).lstrip("\n")
    return metadata, body


def skill_path_priority(path: str) -> tuple[int, int, str]:
    lowered = path.lower()
    for index, prefix in enumerate(PREFERRED_SKILL_ROOTS):
        if lowered.startswith(prefix):
            return index, len(PurePosixPath(path).parts), lowered
    if "/skills/" in lowered:
        return len(PREFERRED_SKILL_ROOTS), len(PurePosixPath(path).parts), lowered
    return len(PREFERRED_SKILL_ROOTS) + 1, len(PurePosixPath(path).parts), lowered


def all_skill_paths(tree_items: list[dict]) -> list[str]:
    paths: list[str] = []
    for entry in tree_items:
        if entry.get("type") != "blob":
            continue
        path = str(entry.get("path") or "")
        parts = {part.lower() for part in PurePosixPath(path).parts}
        if parts & IGNORED_PATH_PARTS:
            continue
        if path == "SKILL.md" or path.endswith("/SKILL.md"):
            paths.append(path)
    return sorted(set(paths), key=skill_path_priority)


def candidate_skill_paths(
    tree_items: list[dict],
    limit: int = MAX_SKILLS_PER_REPOSITORY,
) -> list[str]:
    return all_skill_paths(tree_items)[:limit]


def count_bundled_resources(tree_items: list[dict], skill_path: str) -> dict[str, int]:
    skill_dir = str(PurePosixPath(skill_path).parent)
    if skill_dir == ".":
        skill_dir = ""

    counts = {"scripts": 0, "references": 0, "assets": 0}
    for entry in tree_items:
        if entry.get("type") != "blob":
            continue
        path = str(entry.get("path") or "")
        for resource_name in counts:
            prefix = f"{skill_dir}/{resource_name}/" if skill_dir else f"{resource_name}/"
            if path.startswith(prefix):
                counts[resource_name] += 1
    return counts


def classify_skill_scenario(name: str, description: str, body: str) -> str:
    heading_text = " ".join(
        line.lstrip("#").strip()
        for line in body.splitlines()
        if line.lstrip().startswith("#")
    )
    text = f"{name} {description} {heading_text}".lower()
    best_category = "其他场景"
    best_score = 0

    for category, keywords in SCENARIO_RULES:
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_category = category
            best_score = score

    return best_category


def detect_risk(
    metadata: dict[str, str],
    body: str,
    resources: dict[str, int],
) -> tuple[str, list[str]]:
    text = f"{metadata.get('description', '')} {metadata.get('allowed-tools', '')} {body}".lower()
    reasons: list[str] = []

    for reason, patterns in HIGH_RISK_PATTERNS:
        if any(pattern in text for pattern in patterns):
            reasons.append(reason)

    if reasons:
        return "高", reasons[:3]

    for reason, patterns in MEDIUM_RISK_PATTERNS:
        if any(pattern in text for pattern in patterns):
            reasons.append(reason)

    if resources.get("scripts", 0) > 0:
        reasons.append("包含可执行脚本")
    if metadata.get("allowed-tools"):
        reasons.append("声明了预授权工具")

    if reasons:
        return "中", list(dict.fromkeys(reasons))[:3]
    return "低", ["未发现脚本、预授权工具或明显写入操作"]


def extract_install_hint(body: str) -> str:
    code_lines = []
    in_code_block = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block or not line:
            continue
        lowered = line.lower()
        if any(
            marker in lowered
            for marker in (
                "npx skills add",
                "npm install",
                "pip install",
                "uv add",
                "git clone",
                "claude plugin",
            )
        ):
            code_lines.append(line)

    return trim_text(code_lines[0], 180) if code_lines else ""


def has_trigger_language(description: str) -> bool:
    lowered = description.lower()
    return any(
        phrase in lowered
        for phrase in (
            "use when",
            "use whenever",
            "when the user",
            "whenever",
            "适用于",
            "当用户",
            "用于",
        )
    )


def structure_score(
    metadata: dict[str, str],
    body: str,
    resources: dict[str, int],
    project_license: str,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    name = normalize_text(metadata.get("name"))
    description = normalize_text(metadata.get("description"))
    body_lines = [line for line in body.splitlines() if line.strip()]
    headings = [line for line in body_lines if line.lstrip().startswith("#")]
    lowered_body = body.lower()

    if name:
        score += 10
    if description:
        score += 15
        if 60 <= len(description) <= 1024:
            score += 5
        if has_trigger_language(description):
            score += 10
            reasons.append("触发描述较明确")

    if 20 <= len(body_lines) <= 500:
        score += 10
        reasons.append("主体长度适中")
    elif body_lines:
        score += 5

    if len(headings) >= 3:
        score += 5
    if "example" in lowered_body or "示例" in body:
        score += 10
        reasons.append("包含示例或示范流程")

    resource_total = sum(resources.values())
    if resource_total:
        score += min(15, 5 + resource_total * 2)
        reasons.append("带有按需加载的配套资源")

    optional_metadata = sum(
        bool(normalize_text(metadata.get(field)))
        for field in ("compatibility", "license", "allowed-tools")
    )
    score += min(optional_metadata * 3, 9)

    if project_license not in {"需人工核验", "未标注", ""}:
        score += 6
        reasons.append("仓库许可证信息明确")

    return min(score, 100), reasons[:4]


def score_label(score: int) -> str:
    if score >= 80:
        return "结构完整"
    if score >= 65:
        return "较完整"
    if score >= 45:
        return "基础可读"
    return "信息有限"


def repository_activity_bonus(activity: str) -> int:
    return {"活跃": 6, "较活跃": 4, "一般": 2}.get(activity, 0)


def analyze_skill(
    item: dict,
    path: str,
    raw_text: str,
    tree_items: list[dict],
    *,
    project_license: str,
    project_activity: str,
) -> dict:
    metadata, body = parse_frontmatter(raw_text)
    fallback_name = PurePosixPath(path).parent.name or item.get("name") or "unknown-skill"
    name = normalize_text(metadata.get("name")) or fallback_name
    description = normalize_text(metadata.get("description")) or "SKILL.md 未提供可用的 description。"
    resources = count_bundled_resources(tree_items, path)
    risk_level, risk_reasons = detect_risk(metadata, body, resources)
    base_score, score_reasons = structure_score(
        metadata,
        body,
        resources,
        project_license,
    )
    recommendation_score = (
        base_score
        + repository_activity_bonus(project_activity)
        + (4 if risk_level == "低" else 0)
        - (12 if risk_level == "高" else 0)
    )
    default_branch = item.get("default_branch") or "main"
    encoded_path = quote(path, safe="/")
    url = (
        f"https://github.com/{item.get('full_name')}/blob/"
        f"{quote(str(default_branch), safe='')}/{encoded_path}"
    )

    body_lines = len([line for line in body.splitlines() if line.strip()])
    return {
        "name": name,
        "description": trim_text(description, 360),
        "path": path,
        "url": url,
        "repository": item.get("full_name") or item.get("name") or "未知仓库",
        "repository_url": item.get("html_url") or "",
        "repository_stars": int(item.get("stargazers_count", 0)),
        "project_license": project_license,
        "project_activity": project_activity,
        "declared_license": normalize_text(metadata.get("license")),
        "compatibility": trim_text(metadata.get("compatibility"), 180),
        "allowed_tools": trim_text(metadata.get("allowed-tools"), 180),
        "scenario": classify_skill_scenario(name, description, body),
        "resources": resources,
        "resource_total": sum(resources.values()),
        "body_lines": body_lines,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "structure_score": base_score,
        "structure_label": score_label(base_score),
        "recommendation_score": recommendation_score,
        "recommendation_reasons": score_reasons,
        "install_hint": extract_install_hint(body),
        "frontmatter_complete": bool(metadata.get("name") and metadata.get("description")),
    }


def fetch_repository_tree(
    session: requests.Session,
    item: dict,
    headers: dict[str, str],
) -> tuple[list[dict], bool]:
    repository = item.get("full_name")
    default_branch = item.get("default_branch") or "main"
    if not repository:
        return [], False

    url = (
        f"{GITHUB_API_ROOT}/repos/{repository}/git/trees/"
        f"{quote(str(default_branch), safe='')}"
    )
    response = session.get(
        url,
        headers=headers,
        params={"recursive": "1"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("tree", []), bool(payload.get("truncated"))


def fetch_raw_skill(
    session: requests.Session,
    item: dict,
    path: str,
    headers: dict[str, str],
) -> str:
    repository = item.get("full_name")
    default_branch = item.get("default_branch") or "main"
    if not repository:
        raise RuntimeError("仓库缺少 full_name")

    raw_headers = dict(headers)
    raw_headers["Accept"] = "application/vnd.github.raw+json"
    url = (
        f"{GITHUB_API_ROOT}/repos/{repository}/contents/"
        f"{quote(path, safe='/')}"
    )
    response = session.get(
        url,
        headers=raw_headers,
        params={"ref": default_branch},
        timeout=30,
    )
    response.raise_for_status()
    content = response.content
    if len(content) > MAX_SKILL_BYTES:
        raise RuntimeError(f"SKILL.md 超过 {MAX_SKILL_BYTES // 1000} KB 限制")
    return content.decode("utf-8", errors="replace")


def scan_projects_for_skills(
    items: list[dict],
    headers: dict[str, str],
    project_analyses: list[dict],
    *,
    per_repository_limit: int = MAX_SKILLS_PER_REPOSITORY,
    total_limit: int = MAX_TOTAL_SKILLS,
) -> dict:
    analysis_by_repo = {
        analysis["item"].get("full_name"): analysis for analysis in project_analyses
    }
    session = requests.Session()
    skills: list[dict] = []
    repositories: list[dict] = []
    errors: list[str] = []

    for item in items:
        repository = item.get("full_name") or item.get("name") or "未知仓库"
        project_analysis = analysis_by_repo.get(item.get("full_name"), {})
        project_license = project_analysis.get("license", "需人工核验")
        project_activity = project_analysis.get("activity", "未知")
        repository_summary = {
            "item": item,
            "skills": [],
            "discovered_count": 0,
            "tree_truncated": False,
            "scan_note": "",
        }

        if len(skills) >= total_limit:
            repository_summary["scan_note"] = "达到本期 Skill 分析上限，未继续读取。"
            repositories.append(repository_summary)
            continue

        try:
            tree_items, truncated = fetch_repository_tree(session, item, headers)
            paths = all_skill_paths(tree_items)
            repository_summary["discovered_count"] = len(paths)
            repository_summary["tree_truncated"] = truncated
            selected_paths = paths[: min(per_repository_limit, total_limit - len(skills))]

            for path in selected_paths:
                try:
                    raw_text = fetch_raw_skill(session, item, path, headers)
                    skill = analyze_skill(
                        item,
                        path,
                        raw_text,
                        tree_items,
                        project_license=project_license,
                        project_activity=project_activity,
                    )
                    repository_summary["skills"].append(skill)
                    skills.append(skill)
                except (requests.RequestException, RuntimeError) as exc:
                    errors.append(f"{repository}/{path}：{exc}")

            if truncated:
                repository_summary["scan_note"] = "仓库文件树过大，Skill 数量可能不完整。"
            elif not paths:
                repository_summary["scan_note"] = "未发现 SKILL.md。"
            elif len(paths) > len(selected_paths):
                repository_summary["scan_note"] = (
                    f"发现 {len(paths)} 个 SKILL.md，本期读取前 {len(selected_paths)} 个。"
                )
        except requests.RequestException as exc:
            repository_summary["scan_note"] = "GitHub API 读取失败，已保留仓库层分析。"
            errors.append(f"{repository}：{exc}")

        repositories.append(repository_summary)

    return {
        "skills": skills,
        "repositories": repositories,
        "errors": errors,
        "repositories_with_skills": sum(bool(repo["skills"]) for repo in repositories),
        "discovered_skills": sum(repo["discovered_count"] for repo in repositories),
    }


def recommendation_sort_key(skill: dict) -> tuple:
    return (
        -int(skill.get("recommendation_score", 0)),
        -int(skill.get("structure_score", 0)),
        -int(skill.get("repository_stars", 0)),
        str(skill.get("name", "")).lower(),
    )


def recommend_skills(skills: list[dict], limit: int = 3) -> list[dict]:
    ordered = sorted(skills, key=recommendation_sort_key)
    selected: list[dict] = []
    used_repositories: set[str] = set()

    for skill in ordered:
        repository = str(skill.get("repository"))
        if repository in used_repositories:
            continue
        selected.append(skill)
        used_repositories.add(repository)
        if len(selected) >= limit:
            return selected

    for skill in ordered:
        if skill in selected:
            continue
        selected.append(skill)
        if len(selected) >= limit:
            break
    return selected


def group_skills_by_scenario(skills: list[dict]) -> list[tuple[str, list[dict]]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for skill in skills:
        grouped[str(skill.get("scenario") or "其他场景")].append(skill)

    return sorted(
        (
            (scenario, sorted(group, key=recommendation_sort_key))
            for scenario, group in grouped.items()
        ),
        key=lambda item: (-len(item[1]), item[0]),
    )


def skill_resource_summary(skill: dict) -> str:
    resources = skill.get("resources") or {}
    parts = [
        f"scripts {int(resources.get('scripts', 0))}",
        f"references {int(resources.get('references', 0))}",
        f"assets {int(resources.get('assets', 0))}",
    ]
    return "、".join(parts)


def skill_recommendation_summary(skill: dict) -> str:
    reasons = list(skill.get("recommendation_reasons") or [])
    if not reasons:
        reasons.append("已识别标准 SKILL.md 和基础元数据")
    return "；".join(reasons[:3]) + "。"
