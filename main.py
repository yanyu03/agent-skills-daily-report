import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

TIMEZONE = ZoneInfo("Asia/Shanghai")
SEARCH_ENDPOINT = "https://api.github.com/search/repositories"
SEARCH_QUERY = "mcp-server OR model-context-protocol OR agent-skills"
REPORT_LIMIT = 10

CATEGORY_RULES = (
    {
        "name": "资源导航与项目索引",
        "keywords": (
            "awesome",
            "collection",
            "curated",
            "directory",
            "catalog",
            "resources",
            "list of",
        ),
        "purpose": "汇总 MCP Server、Agent 工具、示例或相关资源，适合先做全局了解和候选项目筛选。",
        "scenarios": "技术调研、寻找现成方案、制作选型清单、补充学习路线。",
        "novice": "先把它当作“项目黄页”使用，按分类、最近更新时间和 README 完整度筛选，不必一次安装全部项目。",
        "developer": "把它作为候选池，再逐个核对协议兼容性、许可证、维护活跃度、部署方式和真实集成成本。",
        "difficulty": "低",
    },
    {
        "name": "低代码自动化与工作流",
        "keywords": (
            "low-code",
            "no-code",
            "workflow automation",
            "visual workflow",
            "automation platform",
            "integrations",
            "visual building",
        ),
        "purpose": "通过可视化节点或预置集成编排 AI、API、数据库和通知流程，减少从零写代码的工作量。",
        "scenarios": "自动收集信息、定时汇总、表单处理、消息通知、AI 内容流水线和内部工具。",
        "novice": "优先使用官方云服务、模板或 Docker 一键部署，从“定时触发 → 调用一个 API → 输出结果”这种三步流程开始。",
        "developer": "适合快速搭建编排层，并用自定义节点、Webhook、队列、数据库和鉴权接入现有系统；生产环境要补日志、重试和密钥管理。",
        "difficulty": "低",
    },
    {
        "name": "命令行智能助手",
        "keywords": (
            "command-line",
            "command line",
            "terminal",
            " cli ",
            "coding agent",
            "code editor",
            "developer assistant",
        ),
        "purpose": "在终端或编辑器中调用模型完成代码解释、生成、修改、检索和自动化任务。",
        "scenarios": "写代码、读仓库、批量修改文件、生成脚本、排查报错和执行开发任务。",
        "novice": "先在测试目录里使用，只让工具解释代码、生成小脚本或修改单个文件；提交前查看 diff，不要直接给高权限。",
        "developer": "可接入仓库规范、测试命令、MCP 工具和 CI；建议设置最小权限、变更审查、超时、成本上限与可回滚提交。",
        "difficulty": "中",
    },
    {
        "name": "MCP Server 与工具接入",
        "keywords": (
            "mcp server",
            "mcp-server",
            "model context protocol",
            "model-context-protocol",
            "mcp tools",
            "mcp integration",
        ),
        "purpose": "把数据库、文件、搜索、业务 API 或外部服务包装成模型可以调用的标准化工具。",
        "scenarios": "给聊天机器人或 Coding Agent 接知识库、文件系统、数据库、浏览器和内部业务能力。",
        "novice": "优先选择带安装命令、示例配置和权限说明的现成 Server；先接只读工具，确认数据范围后再开放写入能力。",
        "developer": "重点检查 transport、schema、鉴权、错误返回、并发、审计和超时；生产接入前应做参数校验与最小权限隔离。",
        "difficulty": "中",
    },
    {
        "name": "多智能体框架与任务编排",
        "keywords": (
            "multi-agent",
            "multi agent",
            "swarm",
            "orchestration",
            "agent framework",
            "agentic framework",
            "agent harness",
            "meta-harness",
            "autonomous workflows",
        ),
        "purpose": "组织多个 Agent、工具和任务步骤，处理角色分工、状态流转、记忆和复杂工作流。",
        "scenarios": "研究型 Agent、代码协作、复杂任务拆解、长流程自动化和多角色模拟。",
        "novice": "不要一开始就搭多 Agent，先跑通一个 Agent 加一个工具的最小示例，再逐步增加角色和步骤。",
        "developer": "需要明确状态机、终止条件、失败恢复、可观测性和 token 预算；多 Agent 不等于更可靠，必须用评测验证收益。",
        "difficulty": "高",
    },
    {
        "name": "RAG、上下文与知识增强",
        "keywords": (
            " rag ",
            "retrieval",
            "context",
            "knowledge",
            "documentation",
            "vector",
            "memory",
            "tool outputs",
            "chunks",
        ),
        "purpose": "为模型补充最新文档、私有知识、检索结果或压缩后的上下文，减少信息过期和无效 token。",
        "scenarios": "本地知识库、代码文档问答、企业资料检索、长上下文优化和开发文档增强。",
        "novice": "先用少量高质量 Markdown 或官方文档测试问答效果，确认引用准确后再扩大资料规模。",
        "developer": "重点评估切分、索引、召回、重排、缓存、引用和成本；不要只看能否回答，还要测答案可追溯性与更新机制。",
        "difficulty": "中",
    },
    {
        "name": "数据采集与网页自动化",
        "keywords": (
            "scraping",
            "scraper",
            "web scraping",
            "crawler",
            "crawl",
            "browser automation",
            "extraction",
        ),
        "purpose": "从网页或接口提取结构化数据，为搜索、知识库、监控或 Agent 提供输入。",
        "scenarios": "采集公开资料、建立数据集、价格或内容监控、网页转 Markdown 和 RAG 数据准备。",
        "novice": "先从单个公开页面和低频任务开始，使用官方示例验证选择器与输出格式，并遵守网站规则和访问频率限制。",
        "developer": "需要处理反爬、重试、代理、去重、调度、结构变化和数据合规；应保存原始响应与解析日志，便于回溯。",
        "difficulty": "中",
    },
    {
        "name": "监控、情报与趋势分析",
        "keywords": (
            "monitor",
            "monitoring",
            "dashboard",
            "intelligence",
            "trend",
            "radar",
            "news aggregation",
            "alert",
            "sentiment",
            "situational awareness",
        ),
        "purpose": "聚合多来源数据并进行筛选、分析、可视化或提醒，帮助持续观察变化。",
        "scenarios": "行业动态、舆情、开源项目、新闻、基础设施、竞品和关键词监控。",
        "novice": "先选少量关键词和一个通知渠道，避免信息过载；连续观察几天后再调整过滤条件。",
        "developer": "可接入 RSS、Webhook、数据库和消息平台，并增加去重、来源可信度、时效性、告警阈值和失败补偿。",
        "difficulty": "低",
    },
    {
        "name": "开发库、平台与基础设施",
        "keywords": (
            "framework",
            "library",
            "sdk",
            "platform",
            "proxy",
            "api",
            "infrastructure",
            "server",
        ),
        "purpose": "提供可编程能力、运行时或基础组件，供开发者组合成自己的 Agent、工具或 AI 应用。",
        "scenarios": "二次开发、构建内部平台、集成模型与工具、封装服务和生产部署。",
        "novice": "先看项目是否提供在线演示、快速开始和完整示例；如果只有 API 或源码，学习成本通常高于成品工具。",
        "developer": "从最小示例开始验证 API 稳定性、扩展点、依赖、许可证和测试覆盖，再决定是否进入核心架构。",
        "difficulty": "高",
    },
)

FALLBACK_CATEGORY = {
    "name": "其他 Agent Skills 与方法论",
    "keywords": (),
    "purpose": "公开元数据不足，暂未能可靠判断主要用途，需要进一步阅读 README 和示例。",
    "scenarios": "方法论、个人 Skills、实验性 Agent 配置或尚未明确归类的工具。",
    "novice": "先查看 README 的安装步骤、示例和权限要求；缺少可运行示例时，不建议直接接入正式环境。",
    "developer": "将其视为待核验候选项，进一步检查仓库结构、最近提交、许可证、测试和真实集成边界。",
    "difficulty": "中",
}

DIFFICULTY_ORDER = {"低": 0, "中": 1, "高": 2}
UNKNOWN_LICENSE_IDS = {"", "NOASSERTION", "OTHER"}


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


def clean_markdown_text(value: str | None, *, table: bool = False) -> str:
    text = " ".join((value or "暂无项目简介。").split())
    return text.replace("|", "\\|") if table else text


def format_updated_at(value: str | None) -> str:
    if not value:
        return "未知"
    try:
        updated_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return updated_at.astimezone(TIMEZONE).strftime("%Y-%m-%d")
    except ValueError:
        return value[:10]


def days_since_update(value: str | None, now: datetime) -> int | None:
    if not value:
        return None
    try:
        updated_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return max((now - updated_at.astimezone(TIMEZONE)).days, 0)
    except ValueError:
        return None


def activity_label(value: str | None, now: datetime) -> str:
    days = days_since_update(value, now)
    if days is None:
        return "未知"
    if days <= 30:
        return "活跃"
    if days <= 90:
        return "较活跃"
    if days <= 180:
        return "一般"
    return "更新较慢"


def language_summary(items: list[dict]) -> str:
    counts = Counter((item.get("language") or "未标注") for item in items)
    return "、".join(
        f"{language}（{count}）" for language, count in counts.most_common(4)
    )


def project_search_text(item: dict) -> str:
    topics = " ".join(item.get("topics") or [])
    return " ".join(
        [
            item.get("name", ""),
            item.get("full_name", ""),
            item.get("description", "") or "",
            topics,
        ]
    ).lower()


def keyword_score(text: str, keyword: str) -> int:
    if keyword.startswith(" ") or keyword.endswith(" "):
        return 2 if keyword in f" {text} " else 0
    return 2 if keyword in text else 0


def classify_project(item: dict) -> dict:
    text = project_search_text(item)
    best_rule: dict | None = None
    best_score = 0

    for rule in CATEGORY_RULES:
        score = sum(keyword_score(text, keyword) for keyword in rule["keywords"])
        if score > best_score:
            best_rule = rule
            best_score = score

    return dict(best_rule or FALLBACK_CATEGORY)


def project_license(item: dict) -> str:
    license_info = item.get("license") or {}
    spdx_id = str(license_info.get("spdx_id") or "").strip()
    license_name = str(license_info.get("name") or "").strip()

    if spdx_id.upper() not in UNKNOWN_LICENSE_IDS:
        return spdx_id
    if license_name and license_name.lower() not in {"other", "unknown"}:
        return license_name
    return "需人工核验"


def project_caution(item: dict, now: datetime) -> str:
    cautions: list[str] = []
    if item.get("archived"):
        cautions.append("仓库已归档")
    if item.get("fork"):
        cautions.append("这是 Fork，需确认上游仓库")
    if project_license(item) == "需人工核验":
        cautions.append("许可证信息不明确，需人工核验")
    activity_time = item.get("pushed_at") or item.get("updated_at")
    days = days_since_update(activity_time, now)
    if days is not None and days > 180:
        cautions.append(f"最近代码推送距今约 {days} 天")
    if not cautions:
        cautions.append("正式采用前仍需验证文档、许可证、维护状态和真实部署成本")
    return "；".join(cautions) + "。"


def project_beginner_advice(item: dict, profile: dict) -> str:
    advice = profile["novice"]
    topics = {str(topic).lower() for topic in item.get("topics") or []}
    description = (item.get("description") or "").lower()
    homepage = item.get("homepage")

    extras: list[str] = []
    if homepage:
        extras.append("可先查看项目主页或在线演示，再决定是否本地安装")
    if "docker" in topics or "docker" in description:
        extras.append("有 Docker 线索时优先使用容器化方案，便于回滚")
    if item.get("language") in {"Python", "TypeScript", "JavaScript", "Go", "Rust"}:
        extras.append("先照 README 跑通最小示例，不要直接改生产环境")
    if extras:
        advice += " " + "；".join(extras) + "。"
    return advice


def project_developer_advice(item: dict, profile: dict) -> str:
    advice = profile["developer"]
    topics = {str(topic).lower() for topic in item.get("topics") or []}
    extras: list[str] = []

    if "docker" in topics:
        extras.append("可先用容器固定依赖，再接入 CI")
    if "api" in topics or "sdk" in topics:
        extras.append("应为外部调用增加超时、重试、限流和错误分类")
    if item.get("open_issues_count", 0) > 500:
        extras.append("Issue 数较多，选型时要抽查维护者响应和关闭速度")
    if extras:
        advice += " " + "；".join(extras) + "。"
    return advice


def analyze_projects(items: list[dict], now: datetime) -> list[dict]:
    analyses: list[dict] = []
    for item in items:
        profile = classify_project(item)
        activity_time = item.get("pushed_at") or item.get("updated_at")
        analyses.append(
            {
                "item": item,
                "profile": profile,
                "activity": activity_label(activity_time, now),
                "license": project_license(item),
                "beginner": project_beginner_advice(item, profile),
                "developer": project_developer_advice(item, profile),
                "caution": project_caution(item, now),
            }
        )
    return analyses


def linked_project(item: dict) -> str:
    name = item.get("full_name", "未知项目")
    url = item.get("html_url", "")
    return f"[{name}]({url})" if url else name


def grouped_scenarios(analyses: list[dict]) -> list[tuple[str, list[dict], dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    profiles: dict[str, dict] = {}
    for analysis in analyses:
        category = analysis["profile"]["name"]
        grouped[category].append(analysis)
        profiles[category] = analysis["profile"]

    ordered_categories = sorted(
        grouped,
        key=lambda category: (
            min(
                DIFFICULTY_ORDER[item["profile"]["difficulty"]]
                for item in grouped[category]
            ),
            -max(
                int(item["item"].get("stargazers_count", 0))
                for item in grouped[category]
            ),
        ),
    )
    return [
        (category, grouped[category], profiles[category])
        for category in ordered_categories
    ]


def generate_report(items: list[dict]) -> Path:
    now = datetime.now(TIMEZONE)
    report_date = now.strftime("%Y-%m-%d")
    report_month = now.strftime("%Y-%m")
    generated_at = now.strftime("%Y-%m-%d %H:%M")

    output_dir = Path("reports") / report_month
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{report_date}.md"

    analyses = analyze_projects(items, now)
    total_stars = sum(int(item.get("stargazers_count", 0)) for item in items)
    category_counts = Counter(
        analysis["profile"]["name"] for analysis in analyses
    )
    category_summary = "、".join(
        f"{category}（{count}）"
        for category, count in category_counts.most_common()
    )

    content = [
        f"# AI Agent Skills 与 MCP 每日观察｜{report_date}",
        "",
        "> [!NOTE]",
        "> 本报告由 GitHub Actions 自动生成，按 GitHub Search API 返回的 Star 数排序，用于观察高关注度项目；它不是 GitHub 官方趋势榜。用途分类和建议由项目名称、简介、Topics 与公开元数据进行规则化判断，适合作为初筛参考，不代替实际试用。",
        "",
        "## 今日概览",
        "",
        f"- **收录项目：** {len(items)} 个",
        f"- **合计 Stars：** {total_stars:,}",
        f"- **主要语言：** {language_summary(items)}",
        f"- **用途分布：** {category_summary}",
        f"- **生成时间：** {generated_at}（Asia/Shanghai）",
        "",
        "## 项目榜单",
        "",
        "| 排名 | 项目 | 用途定位 | 上手门槛 | Stars | 语言 | 活跃度 | 许可证 |",
        "| ---: | --- | --- | --- | ---: | --- | --- | --- |",
    ]

    for rank, analysis in enumerate(analyses, start=1):
        item = analysis["item"]
        profile = analysis["profile"]
        content.append(
            f"| {rank} | {linked_project(item)} | {profile['name']} | "
            f"{profile['difficulty']} | {int(item.get('stargazers_count', 0)):,} | "
            f"{item.get('language') or '未标注'} | {analysis['activity']} | "
            f"{analysis['license']} |"
        )

    content.extend(
        [
            "",
            "## 按用途和场景快速选择",
            "",
            "| 用途 | 本期项目 | 适合场景 | 小白入口 | 开发者关注点 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for category, category_items, profile in grouped_scenarios(analyses):
        project_links = "、".join(
            linked_project(analysis["item"]) for analysis in category_items
        )
        content.append(
            f"| {category} | {project_links} | "
            f"{clean_markdown_text(profile['scenarios'], table=True)} | "
            f"{clean_markdown_text(profile['novice'], table=True)} | "
            f"{clean_markdown_text(profile['developer'], table=True)} |"
        )

    beginner_choices = sorted(
        analyses,
        key=lambda analysis: (
            DIFFICULTY_ORDER[analysis["profile"]["difficulty"]],
            -int(analysis["item"].get("stargazers_count", 0)),
        ),
    )[:3]
    developer_choices = sorted(
        analyses,
        key=lambda analysis: (
            -DIFFICULTY_ORDER[analysis["profile"]["difficulty"]],
            -int(analysis["item"].get("stargazers_count", 0)),
        ),
    )[:3]

    content.extend(
        [
            "",
            "## 人群建议",
            "",
            "### 小白优先看",
            "",
        ]
    )
    for analysis in beginner_choices:
        content.append(
            f"- **{linked_project(analysis['item'])}**："
            f"{analysis['profile']['name']}，上手门槛"
            f"{analysis['profile']['difficulty']}。{analysis['beginner']}"
        )

    content.extend(["", "### 开发者优先看", ""])
    for analysis in developer_choices:
        content.append(
            f"- **{linked_project(analysis['item'])}**："
            f"{analysis['profile']['name']}。{analysis['developer']}"
        )

    content.extend(["", "## 项目逐项说明", ""])
    for rank, analysis in enumerate(analyses, start=1):
        item = analysis["item"]
        profile = analysis["profile"]
        content.extend(
            [
                f"### {rank}. {linked_project(item)}",
                "",
                f"- **用途定位：** {profile['purpose']}",
                f"- **适合场景：** {profile['scenarios']}",
                f"- **项目原始简介：** {clean_markdown_text(item.get('description'))}",
                f"- **小白建议：** {analysis['beginner']}",
                f"- **开发者建议：** {analysis['developer']}",
                f"- **选型提醒：** {analysis['caution']}",
                "",
            ]
        )

    content.extend(
        [
            "## 阅读提示",
            "",
            "- Star 数反映长期关注度，不代表项目当天新增热度。",
            "- 用途分类来自关键词和公开元数据；未可靠命中的项目会明确标记为待核验类别。",
            "- 活跃度优先依据最近代码推送时间，而不是一般仓库元数据更新时间。",
            "- 项目简介保留仓库原文，避免自动翻译造成技术含义偏差。",
            "- 小白建议强调低风险试用路径；开发者建议强调集成、权限、可靠性和生产成本。",
            "- 正式选型前仍需检查 README、许可证、最近提交、Issue 活跃度、安全边界和实际部署成本。",
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