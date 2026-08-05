import unittest
from datetime import datetime

from main import TIMEZONE, analyze_projects, classify_project


class RecommendationRulesTest(unittest.TestCase):
    def test_classifies_common_project_types(self):
        cases = (
            (
                {
                    "name": "awesome-mcp-servers",
                    "description": "A collection of MCP servers.",
                    "topics": ["awesome-list"],
                },
                "资源导航与项目索引",
            ),
            (
                {
                    "name": "agent-cli",
                    "description": "An AI coding agent for the terminal.",
                    "topics": ["cli"],
                },
                "命令行智能助手",
            ),
            (
                {
                    "name": "workflow-tool",
                    "description": "Visual low-code workflow automation platform.",
                    "topics": ["low-code"],
                },
                "低代码自动化与工作流",
            ),
            (
                {
                    "name": "scraper",
                    "description": "A web scraping framework and crawler.",
                    "topics": ["web-scraping"],
                },
                "数据采集与网页自动化",
            ),
        )

        for item, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify_project(item)["name"], expected)

    def test_analysis_contains_both_audience_views(self):
        item = {
            "name": "example-mcp-server",
            "full_name": "example/example-mcp-server",
            "description": "A Model Context Protocol server for files.",
            "topics": ["model-context-protocol"],
            "language": "Python",
            "updated_at": "2026-08-05T00:00:00Z",
            "stargazers_count": 100,
            "license": {"spdx_id": "MIT"},
        }
        now = datetime(2026, 8, 5, 23, 0, tzinfo=TIMEZONE)
        analysis = analyze_projects([item], now)[0]

        self.assertEqual(analysis["profile"]["name"], "MCP Server 与工具接入")
        self.assertIn("只读工具", analysis["beginner"])
        self.assertIn("最小权限", analysis["developer"])
        self.assertEqual(analysis["license"], "MIT")


if __name__ == "__main__":
    unittest.main()
