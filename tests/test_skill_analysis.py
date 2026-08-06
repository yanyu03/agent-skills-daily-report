import unittest

from skill_analysis import (
    analyze_skill,
    candidate_skill_paths,
    classify_skill_scenario,
    count_bundled_resources,
    parse_frontmatter,
    recommend_skills,
)


class SkillAnalysisTest(unittest.TestCase):
    def test_parses_required_and_folded_frontmatter(self):
        metadata, body = parse_frontmatter(
            """---
name: skill-creator
description: >
  Create and improve Agent Skills.
  Use when the user asks to build a skill.
compatibility: Python 3.10+
---
# Skill Creator

Run the workflow.
"""
        )

        self.assertEqual(metadata["name"], "skill-creator")
        self.assertIn("Use when", metadata["description"])
        self.assertEqual(metadata["compatibility"], "Python 3.10+")
        self.assertIn("# Skill Creator", body)

    def test_prefers_standard_skill_roots_and_ignores_vendor_content(self):
        tree = [
            {"type": "blob", "path": "vendor/example/SKILL.md"},
            {"type": "blob", "path": ".claude/skills/review/SKILL.md"},
            {"type": "blob", "path": "skills/create/SKILL.md"},
            {"type": "blob", "path": "plugins/demo/skills/deploy/SKILL.md"},
        ]

        self.assertEqual(
            candidate_skill_paths(tree, limit=3),
            [
                "skills/create/SKILL.md",
                ".claude/skills/review/SKILL.md",
                "plugins/demo/skills/deploy/SKILL.md",
            ],
        )

    def test_counts_bundled_resources_for_one_skill(self):
        tree = [
            {"type": "blob", "path": "skills/demo/SKILL.md"},
            {"type": "blob", "path": "skills/demo/scripts/run.py"},
            {"type": "blob", "path": "skills/demo/references/spec.md"},
            {"type": "blob", "path": "skills/demo/assets/template.txt"},
            {"type": "blob", "path": "skills/other/scripts/ignore.py"},
        ]

        self.assertEqual(
            count_bundled_resources(tree, "skills/demo/SKILL.md"),
            {"scripts": 1, "references": 1, "assets": 1},
        )

    def test_analyzes_skill_structure_scenario_and_risk(self):
        item = {
            "name": "skills",
            "full_name": "example/skills",
            "html_url": "https://github.com/example/skills",
            "default_branch": "main",
            "stargazers_count": 500,
        }
        tree = [
            {"type": "blob", "path": "skills/review/SKILL.md"},
            {"type": "blob", "path": "skills/review/scripts/check.py"},
            {"type": "blob", "path": "skills/review/references/rules.md"},
        ]
        raw = """---
name: reviewing-code
description: Review pull requests and code changes. Use when the user asks for code review or merge readiness.
compatibility: Requires git.
allowed-tools: Bash(git diff:*)
---
# Reviewing Code

## Workflow

Run the review script and inspect the diff.

## Example

Review the current pull request.
"""
        skill = analyze_skill(
            item,
            "skills/review/SKILL.md",
            raw,
            tree,
            project_license="MIT",
            project_activity="活跃",
        )

        self.assertEqual(skill["scenario"], "编程与代码审查")
        self.assertEqual(skill["risk_level"], "中")
        self.assertEqual(skill["resources"]["scripts"], 1)
        self.assertGreaterEqual(skill["structure_score"], 60)

    def test_recommendations_are_diversified_by_repository(self):
        skills = [
            {
                "name": "a",
                "repository": "repo/one",
                "recommendation_score": 90,
                "structure_score": 90,
                "repository_stars": 100,
            },
            {
                "name": "b",
                "repository": "repo/one",
                "recommendation_score": 89,
                "structure_score": 89,
                "repository_stars": 100,
            },
            {
                "name": "c",
                "repository": "repo/two",
                "recommendation_score": 80,
                "structure_score": 80,
                "repository_stars": 50,
            },
        ]

        selected = recommend_skills(skills, limit=2)
        self.assertEqual(
            [skill["repository"] for skill in selected],
            ["repo/one", "repo/two"],
        )

    def test_classifies_document_skill(self):
        self.assertEqual(
            classify_skill_scenario(
                "pdf",
                "Create and edit PDF documents.",
                "# PDF\n## Workflow",
            ),
            "文档与办公",
        )


if __name__ == "__main__":
    unittest.main()
