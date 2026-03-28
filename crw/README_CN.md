# CRW — Dify 工具插件

为 Dify 工作流和 Agent 提供网页抓取、爬取和 URL 映射功能。

CRW 是一个为 AI Agent 打造的开源网页抓取工具。兼容 Firecrawl API，速度快 5.5 倍，内存占用少 75 倍。支持 fastcrw.com 云端或任何自托管 CRW 实例。

## 工具

| 工具 | 端点 | 描述 |
|------|------|------|
| **单页抓取 (Scrape)** | `POST /v1/scrape` | 抓取单个 URL，返回干净的 markdown、HTML、纯文本或结构化 JSON |
| **深度爬取 (Crawl)** | `POST /v1/crawl` | 启动异步 BFS 爬取，支持深度和页面数限制 |
| **爬取状态 (Crawl Status)** | `GET /v1/crawl/{id}` | 查询爬取任务状态或取消运行中的任务 |
| **URL 映射 (Map)** | `POST /v1/map` | 通过链接提取和站点地图解析发现网站上的所有 URL |

## 配置

### 1. 安装插件

从 Dify 市场安装，或在开发期间本地加载：

```bash
# 打包插件
dify plugin package ./crw

# 通过 Dify 设置 > 插件 安装 .difypkg 文件
```

### 2. 配置凭据

| 字段 | 必填 | 描述 |
|------|------|------|
| **CRW API 密钥** | 是 | 从 [fastcrw.com](https://fastcrw.com) 获取的 API 密钥。自托管 CRW 未配置认证时可填任意值。 |
| **CRW 服务器 Base URL** | 否 | 留空使用 fastcrw.com 云端。自托管请填写服务器地址（如 `http://localhost:3000`）。 |

### 配置示例

**fastcrw.com 云端：**
- API 密钥：`fc-your-api-key`
- Base URL：*（留空）*

**自托管 CRW：**
- API 密钥：`any-value`（或您配置的密钥）
- Base URL：`http://localhost:3000`

## 工具详情

### 单页抓取 (Scrape)

从单个 URL 提取干净内容，支持：
- 多种输出格式：markdown、HTML、rawHtml、plainText、links、JSON
- JavaScript 渲染，可配置等待时间
- CSS 选择器和 XPath 精确提取
- 包含/排除标签过滤
- 自定义 HTTP 请求头
- 隐身模式（浏览器请求头、UA 轮换）
- 每请求代理
- 基于 LLM 的结构化提取（通过 JSON Schema）

### 深度爬取 (Crawl)

从 URL 启动异步广度优先爬取：
- 可配置最大深度和最大页面数
- 同步模式（等待完成）或异步模式（返回任务 ID）
- 使用爬取状态工具轮询结果

### 爬取状态 (Crawl Status)

查询或取消运行中的爬取任务：
- 返回当前状态、总页面数、已完成页面数
- 取消操作立即停止爬取

### URL 映射 (Map)

发现网站上的所有 URL：
- 结合链接提取和 sitemap.xml 解析
- 可配置爬取深度
- 返回完整的已发现 URL 列表

## 链接

- [CRW GitHub](https://github.com/crw-org/crw)
- [fastcrw.com](https://fastcrw.com)
- [Dify 插件开发指南](https://docs.dify.ai/zh-hans/develop-plugin/dev-guides-and-walkthroughs/tool-plugin)
