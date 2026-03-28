# CRW Dify Plugin — Integration Plan

## Overview

Build a Dify tool plugin for CRW (fastCRW) that provides web scraping, crawling, and URL mapping capabilities inside Dify workflows and agents. The plugin targets submission to the **Dify Marketplace** via [langgenius/dify-plugins](https://github.com/langgenius/dify-plugins).

CRW's API is Firecrawl-compatible (`/v1/scrape`, `/v1/crawl`, `/v1/map`), so the plugin follows the same pattern as the existing [Firecrawl plugin](https://github.com/langgenius/dify-official-plugins/tree/main/tools/firecrawl) but with CRW-specific branding, fastcrw.com cloud defaults, and better parameter coverage.

---

## 1. Dify Tool Plugin Architecture

### 1.1 Directory Structure

```
crw/
├── _assets/
│   └── icon.svg                    # CRW logo (SVG, required)
├── provider/
│   ├── crw.yaml                    # Provider identity + credentials
│   └── crw.py                      # Provider class (credential validation)
├── tools/
│   ├── crw_client.py               # Shared HTTP client for CRW API
│   ├── scrape.yaml                 # Scrape tool definition
│   ├── scrape.py                   # Scrape tool implementation
│   ├── crawl.yaml                  # Crawl tool definition
│   ├── crawl.py                    # Crawl tool implementation
│   ├── crawl_status.yaml           # Crawl status check tool definition
│   ├── crawl_status.py             # Crawl status check implementation
│   ├── map.yaml                    # Map tool definition
│   └── map.py                      # Map tool implementation
├── main.py                         # Plugin entrypoint
├── manifest.yaml                   # Plugin manifest
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Python project config
├── README.md                       # English documentation
└── README_CN.md                    # Chinese documentation (marketplace req)
```

### 1.2 manifest.yaml

```yaml
author: "us"
created_at: "2026-03-26T00:00:00.000000000Z"
description:
  en_US: >-
    CRW — the open-source web scraper built for AI agents.
    Scrape, crawl, and map websites. Firecrawl-compatible API,
    5.5x faster, 75x less memory. Self-hosted or fastcrw.com cloud.
  zh_Hans: >-
    CRW — 为 AI Agent 打造的开源网页抓取工具。
    抓取、爬取和映射网站。兼容 Firecrawl API，速度快 5.5 倍，内存占用少 75 倍。
    支持自托管或 fastcrw.com 云端。
icon: icon.svg
label:
  en_US: CRW
  zh_Hans: CRW
meta:
  arch:
    - amd64
    - arm64
  runner:
    entrypoint: main
    language: python
    version: "3.12"
  version: 0.0.1
name: crw
plugins:
  tools:
    - provider/crw.yaml
resource:
  memory: 1048576
  permission:
    tool:
      enabled: true
tags:
  - search
  - utilities
type: plugin
version: 0.0.1
```

### 1.3 Provider Definition — `provider/crw.yaml`

```yaml
identity:
  name: crw
  author: us
  label:
    en_US: CRW
    zh_Hans: CRW
  description:
    en_US: >-
      CRW — open-source web scraper built for AI agents.
      Firecrawl-compatible API. Self-hosted or fastcrw.com cloud.
    zh_Hans: >-
      CRW — 为 AI Agent 打造的开源网页抓取工具。
      兼容 Firecrawl API。支持自托管或 fastcrw.com 云端。
  icon: icon.svg
  tags:
    - search
    - utilities

credentials_for_provider:
  base_url:
    type: text-input
    required: false
    label:
      en_US: CRW Server Base URL
      zh_Hans: CRW 服务器 Base URL
    placeholder:
      en_US: https://fastcrw.com/api
    help:
      en_US: >-
        Leave empty to use fastcrw.com cloud. For self-hosted,
        enter your CRW server URL (e.g. http://localhost:3000).
      zh_Hans: >-
        留空使用 fastcrw.com 云端。自托管请输入 CRW 服务器地址
        （例如 http://localhost:3000）。
  api_key:
    type: secret-input
    required: true
    label:
      en_US: CRW API Key
      zh_Hans: CRW API 密钥
    placeholder:
      en_US: fc-your-api-key
    help:
      en_US: >-
        Get your API key from fastcrw.com. For self-hosted CRW
        without auth configured, enter any value.
      zh_Hans: >-
        从 fastcrw.com 获取 API 密钥。如果自托管 CRW
        未配置认证，可以填写任意值。
    url: https://fastcrw.com

tools:
  - tools/scrape.yaml
  - tools/crawl.yaml
  - tools/crawl_status.yaml
  - tools/map.yaml

extra:
  python:
    source: provider/crw.py
```

### 1.4 Provider Implementation — `provider/crw.py`

```python
from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.scrape import ScrapeTool


class CrwProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            for _ in ScrapeTool.from_credentials(credentials, user_id="").invoke(
                tool_parameters={"url": "https://example.com", "formats": "markdown"}
            ):
                pass
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
```

---

## 2. Tool Definitions

### 2.1 Scrape Tool — `tools/scrape.yaml`

```yaml
identity:
  name: scrape
  author: us
  label:
    en_US: Scrape
    zh_Hans: 单页抓取
  description:
    human:
      en_US: Scrape a URL and return clean content as markdown, HTML, plain text, or structured JSON.
      zh_Hans: 抓取 URL 并返回 markdown、HTML、纯文本或结构化 JSON 格式的干净内容。
    llm: >-
      Scrape a single URL and extract its content. Returns markdown by default.
      Supports JS rendering, CSS selectors, XPath, and LLM-based structured extraction.

parameters:
  - name: url
    type: string
    required: true
    form: llm
    label:
      en_US: URL
      zh_Hans: URL
    human_description:
      en_US: The URL to scrape.
      zh_Hans: 要抓取的 URL。
    llm_description: The URL of the webpage to scrape. Required.

  - name: formats
    type: string
    required: false
    form: form
    label:
      en_US: Output Formats
      zh_Hans: 输出格式
    human_description:
      en_US: "Comma-separated output formats: markdown, html, rawHtml, plainText, links, json"
      zh_Hans: "逗号分隔的输出格式：markdown, html, rawHtml, plainText, links, json"
    placeholder:
      en_US: "markdown"

  - name: onlyMainContent
    type: boolean
    required: false
    form: form
    default: true
    label:
      en_US: Only Main Content
      zh_Hans: 仅主要内容
    human_description:
      en_US: Strip navigation, footer, sidebar, and other boilerplate.
      zh_Hans: 去除导航栏、页脚、侧边栏等模板内容。

  - name: renderJs
    type: boolean
    required: false
    form: form
    label:
      en_US: Render JavaScript
      zh_Hans: 渲染 JavaScript
    human_description:
      en_US: "Force JS rendering. Leave unchecked for auto-detection."
      zh_Hans: "强制 JS 渲染。不勾选则自动检测。"

  - name: waitFor
    type: number
    required: false
    form: form
    min: 0
    default: 0
    label:
      en_US: Wait (ms)
      zh_Hans: 等待时间（毫秒）
    human_description:
      en_US: Milliseconds to wait after JS rendering before extracting content.
      zh_Hans: JS 渲染后等待的毫秒数。

  - name: cssSelector
    type: string
    required: false
    form: form
    label:
      en_US: CSS Selector
      zh_Hans: CSS 选择器
    human_description:
      en_US: "Extract only elements matching this CSS selector (e.g. article.post-content)."
      zh_Hans: "仅提取匹配此 CSS 选择器的元素。"

  - name: xpath
    type: string
    required: false
    form: form
    label:
      en_US: XPath
      zh_Hans: XPath
    human_description:
      en_US: "Extract only elements matching this XPath expression."
      zh_Hans: "仅提取匹配此 XPath 表达式的元素。"

  - name: includeTags
    type: string
    required: false
    form: form
    label:
      en_US: Include Tags
      zh_Hans: 包含标签
    human_description:
      en_US: "Comma-separated CSS selectors to include. Example: .content, #main"
      zh_Hans: "逗号分隔的 CSS 选择器。示例：.content, #main"

  - name: excludeTags
    type: string
    required: false
    form: form
    label:
      en_US: Exclude Tags
      zh_Hans: 排除标签
    human_description:
      en_US: "Comma-separated CSS selectors to exclude. Example: .ad, #footer"
      zh_Hans: "逗号分隔的 CSS 选择器。示例：.ad, #footer"

  - name: headers
    type: string
    required: false
    form: form
    label:
      en_US: Custom Headers
      zh_Hans: 自定义请求头
    human_description:
      en_US: 'JSON object of custom HTTP headers. Example: {"Cookie": "session=abc"}'
      zh_Hans: '自定义 HTTP 请求头的 JSON 对象。'

  - name: stealth
    type: boolean
    required: false
    form: form
    label:
      en_US: Stealth Mode
      zh_Hans: 隐身模式
    human_description:
      en_US: Inject browser-like headers and rotate User-Agent to reduce bot detection.
      zh_Hans: 注入浏览器请求头并轮换 User-Agent 以减少机器人检测。

  - name: proxy
    type: string
    required: false
    form: form
    label:
      en_US: Proxy URL
      zh_Hans: 代理 URL
    human_description:
      en_US: "Per-request proxy URL. Example: http://user:pass@proxy:8080"
      zh_Hans: "每请求代理 URL。示例：http://user:pass@proxy:8080"

  - name: jsonSchema
    type: string
    required: false
    form: form
    label:
      en_US: JSON Schema (LLM Extraction)
      zh_Hans: JSON Schema（LLM 提取）
    human_description:
      en_US: >-
        JSON Schema for LLM-based structured extraction.
        Requires LLM config on the CRW server. Returns data in the "json" format.
      zh_Hans: >-
        用于 LLM 结构化提取的 JSON Schema。
        需要在 CRW 服务器上配置 LLM。数据以 "json" 格式返回。

extra:
  python:
    source: tools/scrape.py
```

### 2.2 Crawl Tool — `tools/crawl.yaml`

```yaml
identity:
  name: crawl
  author: us
  label:
    en_US: Crawl
    zh_Hans: 深度爬取
  description:
    human:
      en_US: Start an async BFS crawl from a URL. Returns a job ID for status polling.
      zh_Hans: 从 URL 开始异步 BFS 爬取。返回任务 ID 用于状态查询。
    llm: >-
      Start a web crawl from a given URL. Crawls pages following links up to
      maxDepth and maxPages limits. Returns a job ID that can be polled for results.

parameters:
  - name: url
    type: string
    required: true
    form: llm
    label:
      en_US: Start URL
      zh_Hans: 起始 URL
    llm_description: The URL to start crawling from. Required.

  - name: wait_for_results
    type: boolean
    required: false
    form: form
    default: true
    label:
      en_US: Wait For Results
      zh_Hans: 等待爬取结果
    human_description:
      en_US: >-
        If true, poll until crawl completes (may take minutes for large sites).
        If false, return job ID immediately for async polling.
      zh_Hans: >-
        为 true 时等待爬取完成（大型站点可能需要数分钟）。
        为 false 时立即返回任务 ID 用于异步查询。

  - name: maxDepth
    type: number
    required: false
    form: form
    default: 2
    min: 0
    label:
      en_US: Max Depth
      zh_Hans: 最大深度
    human_description:
      en_US: Maximum link-follow depth from the start URL. 0 = scrape only the start URL.
      zh_Hans: 从起始 URL 开始的最大链接跟随深度。0 = 仅抓取起始 URL。

  - name: maxPages
    type: number
    required: false
    form: form
    default: 100
    min: 1
    label:
      en_US: Max Pages
      zh_Hans: 最大页面数
    human_description:
      en_US: Maximum number of pages to crawl before stopping.
      zh_Hans: 爬取的最大页面数。

  - name: formats
    type: string
    required: false
    form: form
    label:
      en_US: Output Formats
      zh_Hans: 输出格式
    human_description:
      en_US: "Comma-separated formats for each page: markdown, html, rawHtml, plainText, links"
      zh_Hans: "逗号分隔的每页输出格式：markdown, html, rawHtml, plainText, links"

  - name: onlyMainContent
    type: boolean
    required: false
    form: form
    default: true
    label:
      en_US: Only Main Content
      zh_Hans: 仅主要内容

extra:
  python:
    source: tools/crawl.py
```

### 2.3 Crawl Status Tool — `tools/crawl_status.yaml`

```yaml
identity:
  name: crawl_status
  author: us
  label:
    en_US: Crawl Status
    zh_Hans: 爬取状态
  description:
    human:
      en_US: Check the status of a crawl job or cancel it.
      zh_Hans: 查询爬取任务状态或取消任务。
    llm: >-
      Check the status of an async crawl job by its ID.
      Can also cancel a running crawl job.

parameters:
  - name: job_id
    type: string
    required: true
    form: llm
    label:
      en_US: Job ID
      zh_Hans: 任务 ID
    llm_description: The crawl job ID returned by the crawl tool.

  - name: action
    type: select
    required: false
    form: form
    default: status
    label:
      en_US: Action
      zh_Hans: 操作
    options:
      - value: status
        label:
          en_US: Check Status
          zh_Hans: 查询状态
      - value: cancel
        label:
          en_US: Cancel Job
          zh_Hans: 取消任务

extra:
  python:
    source: tools/crawl_status.py
```

### 2.4 Map Tool — `tools/map.yaml`

```yaml
identity:
  name: map
  author: us
  label:
    en_US: Map
    zh_Hans: URL 映射
  description:
    human:
      en_US: Discover all URLs on a website using link extraction and sitemap parsing.
      zh_Hans: 通过链接提取和站点地图解析发现网站上的所有 URL。
    llm: >-
      Discover all URLs on a website. Combines link extraction with sitemap.xml
      parsing to build a complete URL map.

parameters:
  - name: url
    type: string
    required: true
    form: llm
    label:
      en_US: URL
      zh_Hans: URL
    llm_description: The website URL to discover links from. Required.

  - name: maxDepth
    type: number
    required: false
    form: form
    default: 2
    min: 0
    label:
      en_US: Max Depth
      zh_Hans: 最大深度

  - name: useSitemap
    type: boolean
    required: false
    form: form
    default: true
    label:
      en_US: Use Sitemap
      zh_Hans: 使用站点地图
    human_description:
      en_US: Also read and parse sitemap.xml for URL discovery.
      zh_Hans: 同时读取并解析 sitemap.xml 以发现 URL。

extra:
  python:
    source: tools/map.py
```

---

## 3. Tool Implementations

### 3.1 Shared HTTP Client — `tools/crw_client.py`

```python
"""
Shared HTTP client for CRW API.
Handles authentication, retries, and base URL resolution.
"""

import json
import logging
import time
from collections.abc import Mapping
from typing import Any

import requests
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://fastcrw.com/api"


class CrwClient:
    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _request(
        self,
        method: str,
        path: str,
        data: Mapping[str, Any] | None = None,
        retries: int = 3,
        backoff_factor: float = 0.3,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        for i in range(retries):
            try:
                resp = requests.request(
                    method, url, json=data, headers=self._headers(), timeout=120
                )
                result = resp.json()
                if not result.get("success", True):
                    error_msg = result.get("error", "Unknown error")
                    raise HTTPError(f"CRW API error: {error_msg}")
                return result
            except requests.exceptions.RequestException:
                if i < retries - 1:
                    time.sleep(backoff_factor * (2**i))
                else:
                    raise
        raise HTTPError("Request failed after retries")

    def scrape(self, url: str, **kwargs) -> dict[str, Any]:
        return self._request("POST", "/v1/scrape", {"url": url, **kwargs})

    def crawl(self, url: str, **kwargs) -> dict[str, Any]:
        return self._request("POST", "/v1/crawl", {"url": url, **kwargs})

    def crawl_status(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/crawl/{job_id}")

    def cancel_crawl(self, job_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v1/crawl/{job_id}")

    def map(self, url: str, **kwargs) -> dict[str, Any]:
        return self._request("POST", "/v1/map", {"url": url, **kwargs})

    def poll_crawl(self, job_id: str, interval: int = 5) -> dict[str, Any]:
        while True:
            status = self.crawl_status(job_id)
            if status.get("status") == "completed":
                return status
            if status.get("status") == "failed":
                raise HTTPError(f"Crawl failed: {status.get('error', 'unknown')}")
            time.sleep(interval)


def get_array_params(params: dict[str, Any], key: str) -> list[str] | None:
    value = params.get(key)
    if value and isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return None


def get_json_params(params: dict[str, Any], key: str) -> Any | None:
    value = params.get(key)
    if value and isinstance(value, str):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in parameter '{key}'")
    return None
```

### 3.2 Scrape Implementation — `tools/scrape.py`

```python
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, get_array_params, get_json_params


class ScrapeTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        payload["formats"] = get_array_params(tool_parameters, "formats") or ["markdown"]
        payload["onlyMainContent"] = tool_parameters.get("onlyMainContent", True)

        # Optional parameters — only include if set
        if tool_parameters.get("renderJs") is not None:
            payload["renderJs"] = tool_parameters["renderJs"]
        if tool_parameters.get("waitFor"):
            payload["waitFor"] = tool_parameters["waitFor"]
        if tool_parameters.get("cssSelector"):
            payload["cssSelector"] = tool_parameters["cssSelector"]
        if tool_parameters.get("xpath"):
            payload["xpath"] = tool_parameters["xpath"]
        if tool_parameters.get("stealth") is not None:
            payload["stealth"] = tool_parameters["stealth"]
        if tool_parameters.get("proxy"):
            payload["proxy"] = tool_parameters["proxy"]

        include_tags = get_array_params(tool_parameters, "includeTags")
        if include_tags:
            payload["includeTags"] = include_tags
        exclude_tags = get_array_params(tool_parameters, "excludeTags")
        if exclude_tags:
            payload["excludeTags"] = exclude_tags

        headers = get_json_params(tool_parameters, "headers")
        if headers:
            payload["headers"] = headers

        json_schema = get_json_params(tool_parameters, "jsonSchema")
        if json_schema:
            payload["jsonSchema"] = json_schema
            if "json" not in payload["formats"]:
                payload["formats"].append("json")

        # Clean None values
        payload = {k: v for k, v in payload.items() if v is not None}

        result = client.scrape(url=tool_parameters["url"], **payload)

        # Yield markdown as text for direct display in chat
        data = result.get("data", {})
        markdown = data.get("markdown", "")
        if markdown:
            yield self.create_text_message(markdown)

        # Yield full response as JSON for workflow consumption
        yield self.create_json_message(result)
```

### 3.3 Crawl Implementation — `tools/crawl.py`

```python
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, get_array_params


class CrawlTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        if tool_parameters.get("maxDepth") is not None:
            payload["maxDepth"] = tool_parameters["maxDepth"]
        if tool_parameters.get("maxPages") is not None:
            payload["maxPages"] = tool_parameters["maxPages"]
        if tool_parameters.get("onlyMainContent") is not None:
            payload["onlyMainContent"] = tool_parameters["onlyMainContent"]
        formats = get_array_params(tool_parameters, "formats")
        if formats:
            payload["formats"] = formats

        wait = tool_parameters.get("wait_for_results", True)

        # Start crawl
        result = client.crawl(url=tool_parameters["url"], **payload)

        if wait and result.get("id"):
            # Poll until complete
            result = client.poll_crawl(result["id"])

        yield self.create_json_message(result)

        # If completed, also yield summary text
        if result.get("status") == "completed":
            total = result.get("total", 0)
            completed = result.get("completed", 0)
            yield self.create_text_message(
                f"Crawl completed: {completed}/{total} pages scraped."
            )
        elif result.get("id"):
            yield self.create_text_message(
                f"Crawl started. Job ID: {result['id']}"
            )
```

### 3.4 Crawl Status Implementation — `tools/crawl_status.py`

```python
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient


class CrawlStatusTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        job_id = tool_parameters["job_id"]
        action = tool_parameters.get("action", "status")

        if action == "cancel":
            result = client.cancel_crawl(job_id)
            yield self.create_text_message(f"Crawl job {job_id} cancelled.")
        else:
            result = client.crawl_status(job_id)
            status = result.get("status", "unknown")
            total = result.get("total", 0)
            completed = result.get("completed", 0)
            yield self.create_text_message(
                f"Crawl {job_id}: {status} ({completed}/{total} pages)"
            )

        yield self.create_json_message(result)
```

### 3.5 Map Implementation — `tools/map.py`

```python
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient


class MapTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        if tool_parameters.get("maxDepth") is not None:
            payload["maxDepth"] = tool_parameters["maxDepth"]
        if tool_parameters.get("useSitemap") is not None:
            payload["useSitemap"] = tool_parameters["useSitemap"]

        result = client.map(url=tool_parameters["url"], **payload)

        links = result.get("data", {}).get("links", [])
        yield self.create_text_message(
            f"Found {len(links)} URLs:\n" + "\n".join(links[:50])
            + (f"\n... and {len(links) - 50} more" if len(links) > 50 else "")
        )
        yield self.create_json_message(result)
```

### 3.6 Entrypoint — `main.py`

```python
from dify_plugin import Plugin, DifyPluginEnv

plugin = Plugin(DifyPluginEnv())

if __name__ == "__main__":
    plugin.run()
```

### 3.7 Dependencies — `requirements.txt`

```
dify_plugin>=0.3.0,<0.6.0
requests>=2.31.0,<3.0.0
```

---

## 4. Configuration: Self-Hosted vs Cloud

The plugin supports both deployment modes via the `base_url` credential:

| Mode | `base_url` value | `api_key` value |
|---|---|---|
| **fastcrw.com cloud** | Empty (defaults to `https://fastcrw.com/api`) | API key from fastcrw.com dashboard |
| **Self-hosted** | `http://localhost:3000` or custom URL | Any value (if auth not configured) or configured API key |

The default points to fastcrw.com, which drives cloud signups. Self-hosted users just override the base URL — same API, zero code changes.

---

## 5. Differentiation from Firecrawl Plugin

| Feature | CRW Plugin | Firecrawl Plugin |
|---|---|---|
| Default cloud endpoint | fastcrw.com (free tier) | api.firecrawl.dev (paid) |
| CSS Selector / XPath | Native parameters | Not exposed |
| Stealth mode | Per-request toggle | Not available |
| Per-request proxy | Supported | Not available |
| JS rendering control | `renderJs` param (auto/force/disable) | Not exposed |
| LLM extraction | Via `jsonSchema` param | Via `schema` + `systemPrompt` |
| Crawl cancel | Dedicated tool | Combined in crawl_job tool |
| API client | Clean typed client | Hand-rolled with legacy patterns |
| `dify_plugin` version | >=0.3.0 (current) | 0.0.1b65 (outdated) |

---

## 6. Implementation Tasks

### Phase 1: Build Plugin (Day 1-2)

- [ ] **T1.1** — Scaffold project with `dify plugin init`
- [ ] **T1.2** — Create `_assets/icon.svg` (CRW logo)
- [ ] **T1.3** — Write `manifest.yaml`
- [ ] **T1.4** — Write `provider/crw.yaml` + `provider/crw.py`
- [ ] **T1.5** — Write `tools/crw_client.py` (shared HTTP client)
- [ ] **T1.6** — Write `tools/scrape.yaml` + `tools/scrape.py`
- [ ] **T1.7** — Write `tools/crawl.yaml` + `tools/crawl.py`
- [ ] **T1.8** — Write `tools/crawl_status.yaml` + `tools/crawl_status.py`
- [ ] **T1.9** — Write `tools/map.yaml` + `tools/map.py`
- [ ] **T1.10** — Write `main.py`, `requirements.txt`, `pyproject.toml`

### Phase 2: Test (Day 2-3)

- [ ] **T2.1** — Local debug with Dify dev instance (`INSTALL_METHOD=remote`)
- [ ] **T2.2** — Test credential validation (both cloud and self-hosted)
- [ ] **T2.3** — Test scrape tool in Chatflow + Agent
- [ ] **T2.4** — Test crawl tool (sync wait + async job ID)
- [ ] **T2.5** — Test crawl status (check + cancel)
- [ ] **T2.6** — Test map tool
- [ ] **T2.7** — Test all tools in a Workflow node
- [ ] **T2.8** — Package: `dify plugin package ./crw` → verify `.difypkg`

### Phase 3: Documentation (Day 3)

- [ ] **T3.1** — Write `README.md` (English): overview, setup, tool descriptions, examples
- [ ] **T3.2** — Write `README_CN.md` (Chinese): same content translated
- [ ] **T3.3** — Add screenshots of tools in Dify workflow UI

### Phase 4: Submit to Marketplace (Day 3-4)

- [ ] **T4.1** — Fork `langgenius/dify-plugins`
- [ ] **T4.2** — Add plugin under `tools/crw/` directory
- [ ] **T4.3** — Ensure compliance with marketplace requirements:
  - manifest.yaml author must not contain "dify" or "langgenius"
  - Real icon (no placeholder)
  - English README.md, Chinese README_CN.md
  - Works on Dify Community Edition + Cloud
- [ ] **T4.4** — Open PR following the [plugin PR template](https://github.com/langgenius/dify-plugins/pulls)
- [ ] **T4.5** — Respond to review feedback

---

## 7. PR Strategy

### Target Repository

**`langgenius/dify-plugins`** (community marketplace) — NOT `dify-official-plugins` (maintained by Dify team only).

### PR Title

```
feat: add CRW web scraping tool plugin
```

### PR Description Template

```markdown
## Plugin Information

- **Name**: CRW
- **Type**: Tool
- **Category**: Search, Utilities
- **Author**: us

## Description

CRW is an open-source web scraper built for AI agents. This plugin provides
4 tools: Scrape, Crawl, Crawl Status, and Map.

- **Firecrawl-compatible API** — same endpoint family, familiar interface
- **5.5x faster, 75x less memory** than Firecrawl
- **Self-hosted or cloud** — defaults to fastcrw.com, supports any CRW instance
- **Advanced features** — CSS selectors, XPath, stealth mode, per-request proxy,
  JS rendering control, LLM structured extraction

## Tools

| Tool | Description |
|------|-------------|
| Scrape | Scrape a URL → markdown/HTML/JSON |
| Crawl | Async BFS crawl with depth/page limits |
| Crawl Status | Check/cancel crawl jobs |
| Map | Discover all URLs on a website |

## Checklist

- [x] Read and followed "Publish to Dify Marketplace" guidelines
- [x] Read and comply with Plugin Developer Agreement
- [x] Plugin works on Dify Community Edition
- [x] Plugin works on Dify Cloud Version
- [x] Thorough testing completed
- [x] Plugin brings new value to Dify (faster, lighter alternative to Firecrawl)
```

---

## 8. Post-Launch

- Add "Dify" to the CRW README.md integrations list
- Add Dify integration section to fastcrw.com docs
- Write a blog post: "Using CRW in Dify Workflows for RAG"
- Monitor Dify marketplace reviews and issue tracker
- Keep plugin updated with new CRW API features (chunking, filtering)

---

## References

- [Dify Tool Plugin Development Guide](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-plugin)
- [Dify Plugin Marketplace](https://github.com/langgenius/dify-plugins)
- [Dify Official Plugins (Firecrawl reference)](https://github.com/langgenius/dify-official-plugins/tree/main/tools/firecrawl)
- [CRW REST API Reference](/Users/us/coding/crw/crw-opencore/docs/docs/rest-api.md)
- [CRW README](/Users/us/coding/crw/crw-opencore/README.md)
- [fastcrw.com](https://fastcrw.com)
