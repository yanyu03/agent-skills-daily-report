# Cloudflare Pages 缓存审计

- **生成时间：** 2026-08-07 01:06:33 UTC
- **Pages 项目：** `agent-skills-daily-report`
- **自定义域名：** `skill.250221.xyz`
- **Zone：** `250221.xyz`
- **安全说明：** 报告不输出 API Token 或完整 Account ID。

## Pages 项目状态

- **API 状态：** 正常（HTTP 200）
- **生产分支：** `blog`
- **pages.dev：** `https://agent-skills-daily-report-2ep.pages.dev`
- **绑定域名：** `agent-skills-daily-report-2ep.pages.dev`, `report.takaosakuma.dpdns.org`
- **最近部署 ID：** `e259e498-e31b-490e-b1cf-9fa0adcfa1d5`
- **最近部署环境：** `production`
- **最近部署时间：** `2026-08-07T00:53:50.272414Z`
- **最近部署地址：** `https://e259e498.agent-skills-daily-report-2ep.pages.dev`

## Zone 与缓存设置

无法读取 Zone（HTTP 200，未返回详细错误）。API Token 可能只有 Pages 权限，没有 Zone/Rulesets 读取权限。

## 内容与响应头对照

比较 `blog` 分支文件、pages.dev 和自定义域名。查询参数请求同时携带 `Cache-Control: no-cache`。

| 文件 | 本地 | pages.dev | 自定义域名 | 自定义域名（绕缓存） |
| --- | --- | --- | --- | --- |
| `/index.html` | `8836cd1fda29` / 11217 B | HTTP 200<br>匹配本地：**是** | HTTP 0<br>匹配本地：**否** | HTTP 0<br>匹配本地：**否** |
| `/post/5.html` | `44073150fb17` / 49439 B | HTTP 200<br>匹配本地：**是** | HTTP 0<br>匹配本地：**否** | HTTP 0<br>匹配本地：**否** |
| `/assets/skill-report.css` | `33c75f0bebc2` / 42174 B | HTTP 200<br>匹配本地：**是** | HTTP 0<br>匹配本地：**否** | HTTP 0<br>匹配本地：**否** |

### 自定义域名响应头

#### `/index.html`

**普通请求**

**CF-Cache-Status:** `-`<br>**Age:** `-`<br>**Cache-Control:** `-`<br>**CDN-Cache-Control:** `-`<br>**ETag:** `-`<br>**Last-Modified:** `-`<br>**CF-Ray:** `-`

**带查询参数与 no-cache 请求**

**CF-Cache-Status:** `-`<br>**Age:** `-`<br>**Cache-Control:** `-`<br>**CDN-Cache-Control:** `-`<br>**ETag:** `-`<br>**Last-Modified:** `-`<br>**CF-Ray:** `-`

#### `/post/5.html`

**普通请求**

**CF-Cache-Status:** `-`<br>**Age:** `-`<br>**Cache-Control:** `-`<br>**CDN-Cache-Control:** `-`<br>**ETag:** `-`<br>**Last-Modified:** `-`<br>**CF-Ray:** `-`

**带查询参数与 no-cache 请求**

**CF-Cache-Status:** `-`<br>**Age:** `-`<br>**Cache-Control:** `-`<br>**CDN-Cache-Control:** `-`<br>**ETag:** `-`<br>**Last-Modified:** `-`<br>**CF-Ray:** `-`

#### `/assets/skill-report.css`

**普通请求**

**CF-Cache-Status:** `-`<br>**Age:** `-`<br>**Cache-Control:** `-`<br>**CDN-Cache-Control:** `-`<br>**ETag:** `-`<br>**Last-Modified:** `-`<br>**CF-Ray:** `-`

**带查询参数与 no-cache 请求**

**CF-Cache-Status:** `-`<br>**Age:** `-`<br>**Cache-Control:** `-`<br>**CDN-Cache-Control:** `-`<br>**ETag:** `-`<br>**Last-Modified:** `-`<br>**CF-Ray:** `-`

## 自动诊断

> pages.dev 已更新，但自定义域名即使带随机查询参数仍不一致；优先检查自定义域名映射、忽略查询参数的缓存键规则或 Worker 路由。

### 判断矩阵

- **pages.dev 全部匹配本地：** 是
- **自定义域名普通请求全部匹配：** 否
- **自定义域名绕缓存请求全部匹配：** 否

