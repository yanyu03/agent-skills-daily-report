import os
import requests
from datetime import datetime

def fetch_mcp_servers():
      domain = '.'.join(['api', 'github', 'com'])
      base_url = "https://" + domain + "/search/repositories"
      query = "?q=mcp-server+OR+model-context-protocol&sort=stars&order=desc"
      url = base_url + query
      headers = {"Accept": "application/vnd.github.v3+json"}
      try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                return response.json().get("items", [])[:10]
          except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def generate_report(items):
      now = datetime.utcnow()
      report_date = now.strftime("%Y-%m-%d")
      report_month = now.strftime("%Y-%m")

    os.makedirs(f"reports/{report_month}", exist_ok=True)
    filepath = f"reports/{report_month}/{report_date}.md"

    content = f"# Daily AI Agent Skills & MCP Servers Report - {report_date}\n\n"
    content += "Here is the list of top trending Model Context Protocol (MCP) servers and Agent Skill repositories today:\n\n"
    content += "| Repository | Description | Stars | Language | Link |\n"
    content += "| --- | --- | --- | --- | --- |\n"

    for item in items:
              name = item.get("full_name", "")
              desc = item.get("description", "") or "No description provided."
              stars = item.get("stargazers_count", 0)
              lang = item.get("language", "") or "N/A"
              url = item.get("html_url", "")
              content += f"| {name} | {desc} | {stars} | {lang} | [Link]({url}) |\n"

    with open(filepath, "w", encoding="utf-8") as f:
              f.write(content)
          print(f"Report successfully saved to {filepath}")

if __name__ == "__main__":
      servers = fetch_mcp_servers()
      generate_report(servers)
  
