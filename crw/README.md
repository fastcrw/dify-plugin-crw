# fastCRW Dify Tool Plugin

Web scraping, crawling, URL mapping, search, and structured extraction for Dify
workflows and agents.

fastCRW is the open-source web data API built for AI agents. Point it at the
fastcrw.com cloud with an API key, or self-host the single 8 MB binary.

Source: https://github.com/us/dify-plugin-crw

## Tools

| Tool | Endpoint | Description |
|------|----------|-------------|
| **Scrape** | `POST /v1/scrape` | Read one page as markdown, HTML, plain text, links, or structured JSON |
| **Crawl** | `POST /v1/crawl` | Read many pages of a site by following links |
| **Crawl Status** | `GET /v1/crawl/{id}` | Check or cancel a crawl job |
| **Map** | `POST /v1/map` | Discover every URL on a site, without reading page content |
| **Search** | `POST /v1/search` | Search the web, optionally scraping results or synthesising an answer |
| **Extract** | `POST /v1/extract` | Pull the same structured fields from several URLs at once |

Every tool declares an `output_schema`, so its outputs appear as named variables
in the Dify variable picker instead of raw JSON you have to path into by hand.

## Setup

### 1. Install the plugin

Install from the Dify Marketplace, or build it locally:

```bash
dify plugin package ./crw
```

Then install the resulting `.difypkg` from Dify Settings > Plugins.

### 2. Configure credentials

#### Recommended: fastcrw.com cloud

[Sign up at fastcrw.com](https://fastcrw.com) for **500 free credits**, no card
required.

- **API Key:** your `crw_live_...` key
- **Base URL:** leave empty, it defaults to `https://fastcrw.com/api`

#### Alternative: self-host

```bash
curl -fsSL https://fastcrw.com/install | sh
crw serve
```

- **API Key:** any value, if your server runs without auth
- **Base URL:** your server, for example `http://localhost:3000`

Search needs a cloud key. Extract works on both, and the plugin handles the
difference for you: the cloud runs it synchronously, a self-hosted server runs it
as a job and the tool polls until it finishes.

On the cloud, Extract needs a paid plan, as do the LLM-backed options (`summary`
format, prompt or JSON Schema extraction, and search `answer` /
`summarizeResults`).

## Notes

- **Credits.** One credit per page. A crawl of 100 pages costs 100 credits.
  Turning on `scrapeResults` in Search costs one credit per result.
- **Long crawls.** Crawl waits for results by default. If the job is still
  running after about four minutes it returns the job ID plus the pages
  collected so far, so nothing is lost. Poll it with the Crawl Status tool.
- **Agent use.** Parameters an agent should choose from the user's question
  (URL, query, formats, time filter, language, sources, categories) are exposed
  to the model. Parameters that spend credits or configure the environment are
  operator-set on the node.
- **Domain scoping in Search.** There is no `includeDomains` parameter; use the
  `site:` operator in the query, for example `site:docs.python.org asyncio`.
- **Crawl path filters.** Unlike some other crawlers, fastCRW's crawl API has no
  `includePaths` / `excludePaths`. Use Map to list URLs, filter them in your
  workflow, then Scrape the ones you want.

## Links

- [fastCRW](https://fastcrw.com)
- [fastCRW engine on GitHub](https://github.com/us/crw)
- [API docs](https://docs.fastcrw.com)
