# CRW — Dify Tool Plugin

Web scraping, crawling, and URL mapping for Dify workflows and agents.

CRW is an open-source web scraper built for AI agents. Firecrawl-compatible API, 5.5x faster, 75x less memory. Works with fastcrw.com cloud or any self-hosted CRW instance.

## Tools

| Tool | Endpoint | Description |
|------|----------|-------------|
| **Scrape** | `POST /v1/scrape` | Scrape a single URL and return clean markdown, HTML, plain text, or structured JSON |
| **Crawl** | `POST /v1/crawl` | Start an async BFS crawl with depth and page limits |
| **Crawl Status** | `GET /v1/crawl/{id}` | Check crawl job status or cancel a running job |
| **Map** | `POST /v1/map` | Discover all URLs on a website via link extraction and sitemap parsing |

## Setup

### 1. Install the Plugin

Install from the Dify Marketplace, or load locally during development:

```bash
# Package the plugin
dify plugin package ./crw

# Install the .difypkg file via Dify Settings > Plugins
```

### 2. Configure Credentials — Pick One

#### Option A: Cloud ([fastcrw.com](https://fastcrw.com)) — Quickest Start

[Sign up at fastcrw.com](https://fastcrw.com) and get **500 free credits**:

- **API Key:** `crw_live_...` from fastcrw.com
- **Base URL:** *(leave empty — defaults to fastcrw.com)*

#### Option B: Self-hosted with binary (free, no limits)

```bash
curl -fsSL https://raw.githubusercontent.com/us/crw/main/install.sh | bash
crw  # starts on http://localhost:3000
```

- **API Key:** `any-value` (or leave empty if no auth)
- **Base URL:** `http://localhost:3000`

#### Option C: Self-hosted with Docker

```bash
docker run -d -p 3000:3000 ghcr.io/us/crw:latest
```

Same as Option B.

## Tool Details

### Scrape

Extract clean content from a single URL. Supports:
- Multiple output formats: markdown, HTML, rawHtml, plainText, links, JSON
- JavaScript rendering with configurable wait time
- CSS selectors and XPath for targeted extraction
- Include/exclude tag filters
- Custom HTTP headers
- Stealth mode (browser-like headers, UA rotation)
- Per-request proxy
- LLM-based structured extraction via JSON Schema

### Crawl

Start an async breadth-first crawl from a URL:
- Configurable max depth and max pages
- Sync mode (wait for completion) or async mode (return job ID)
- Poll for results using the Crawl Status tool

### Crawl Status

Check on or cancel a running crawl job:
- Returns current status, total pages, completed pages
- Cancel action stops the crawl immediately

### Map

Discover all URLs on a website:
- Combines link extraction with sitemap.xml parsing
- Configurable crawl depth
- Returns a complete list of discovered URLs

## Links

- [CRW GitHub](https://github.com/us/crw)
- [fastcrw.com](https://fastcrw.com)
- [Dify Plugin Development Guide](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-plugin)
