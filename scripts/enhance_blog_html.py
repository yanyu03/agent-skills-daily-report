from __future__ import annotations

import argparse
import re
from pathlib import Path

POST_BODY_MARKER = '<div class="markdown-body" id="postBody">'
POST_BODY_REPLACEMENT = (
    '<div class="markdown-body skill-prose skill-prose-slate '
    'dark:skill-prose-invert max-w-none skill-report" id="postBody">'
)


def enhance_recommendations(document: str) -> str:
    start_marker = "<h2>今日推荐 Skill</h2>"
    end_marker = "<h2>按使用场景浏览 Skill</h2>"
    start = document.find(start_marker)
    end = document.find(end_marker)
    if start < 0 or end < 0 or end <= start:
        return document

    prefix = document[:start]
    section = document[start:end]
    suffix = document[end:]

    section = section.replace(
        start_marker,
        '<h2 class="section-heading section-heading--featured">今日推荐 Skill</h2>',
        1,
    )
    card_pattern = re.compile(
        r"(<h3>.*?</h3>\s*<blockquote>.*?</blockquote>\s*<ul>.*?</ul>)",
        re.DOTALL,
    )
    section = card_pattern.sub(
        lambda match: f'<article class="skill-card">{match.group(1)}</article>',
        section,
    )
    return prefix + section + suffix


def enhance_post_html(document: str) -> str:
    document = document.replace(
        "<body>",
        '<body class="skill-site skill-post-page">',
        1,
    )
    document = document.replace(
        POST_BODY_MARKER,
        POST_BODY_REPLACEMENT,
        1,
    )
    document = document.replace(
        "<h2>今日概览</h2>\n<ul>",
        '<h2 class="section-heading section-heading--overview">今日概览</h2>\n'
        '<ul class="metric-grid">',
        1,
    )
    document = enhance_recommendations(document)
    document = document.replace(
        "<h2>按使用场景浏览 Skill</h2>",
        '<h2 class="section-heading section-heading--scenario">按使用场景浏览 Skill</h2>',
        1,
    )
    document = document.replace(
        "<h2>仓库—Skill 目录</h2>",
        '<h2 class="section-heading section-heading--directory">仓库—Skill 目录</h2>',
        1,
    )
    document = document.replace(
        "<h2>高关注仓库榜单</h2>",
        '<h2 class="section-heading section-heading--repository">高关注仓库榜单</h2>',
        1,
    )
    document = document.replace(
        "<markdown-accessiblity-table>",
        '<markdown-accessiblity-table class="table-scroll">',
    )
    document = document.replace("<details>", '<details class="skill-details">')
    return document


def enhance_index_html(document: str) -> str:
    document = document.replace(
        "<body>",
        '<body class="skill-site skill-home-page">',
        1,
    )
    document = document.replace(
        '<nav class="SideNav border">',
        '<nav class="SideNav border skill-post-list">',
        1,
    )
    return document


def enhance_document(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    if path.name == "index.html":
        enhanced = enhance_index_html(original)
    elif path.parent.name == "post":
        enhanced = enhance_post_html(original)
    else:
        enhanced = original.replace(
            "<body>",
            '<body class="skill-site">',
            1,
        )

    if enhanced == original:
        return False
    path.write_text(enhanced, encoding="utf-8")
    return True


def enhance_site(root: Path) -> int:
    changed = 0
    for path in sorted(root.rglob("*.html")):
        changed += int(enhance_document(path))
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add scoped semantic classes to Gmeek HTML before Tailwind compilation."
    )
    parser.add_argument("docs_dir", type=Path)
    args = parser.parse_args()

    if not args.docs_dir.is_dir():
        raise SystemExit(f"HTML directory does not exist: {args.docs_dir}")

    changed = enhance_site(args.docs_dir)
    print(f"Enhanced {changed} HTML files in {args.docs_dir}")


if __name__ == "__main__":
    main()
