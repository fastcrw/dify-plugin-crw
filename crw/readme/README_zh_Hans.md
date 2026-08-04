# fastCRW Dify 工具插件

为 Dify 工作流和 Agent 提供网页抓取、爬取、URL 映射、搜索和结构化提取能力。

fastCRW 是为 AI Agent 打造的开源网页数据 API。使用 API 密钥连接 fastcrw.com 云端，
或自托管仅 8 MB 的单一二进制文件。

源码：https://github.com/us/dify-plugin-crw

## 工具

| 工具 | 接口 | 说明 |
|------|------|------|
| **Scrape** | `POST /v1/scrape` | 读取单个页面，返回 markdown、HTML、纯文本、链接或结构化 JSON |
| **Crawl** | `POST /v1/crawl` | 跟随链接读取站点的多个页面 |
| **Crawl Status** | `GET /v1/crawl/{id}` | 查询或取消爬取任务 |
| **Map** | `POST /v1/map` | 发现站点上的所有 URL，不读取页面内容 |
| **Search** | `POST /v1/search` | 搜索网页，可选抓取结果或综合生成答案 |
| **Extract** | `POST /v1/extract` | 从多个 URL 中一次性提取相同的结构化字段 |

每个工具都声明了 `output_schema`，因此其输出会作为具名变量出现在 Dify 的变量选择器中，
无需手写 JSON 路径。

## 配置

### 1. 安装插件

从 Dify 市场安装，或在本地构建：

```bash
dify plugin package ./crw
```

然后在 Dify 设置 > 插件中安装生成的 `.difypkg` 文件。

### 2. 配置凭据

#### 推荐：fastcrw.com 云端

在 [fastcrw.com](https://fastcrw.com) 注册可获得 **500 个免费积分**，无需信用卡。

- **API 密钥：** 你的 `crw_live_...` 密钥
- **Base URL：** 留空，默认使用 `https://fastcrw.com/api`

#### 备选：自托管

```bash
curl -fsSL https://fastcrw.com/install | sh
crw serve
```

- **API 密钥：** 若服务器未配置认证，可填写任意值
- **Base URL：** 你的服务器地址，例如 `http://localhost:3000`

Search 需要云端密钥。Extract 两者都支持，插件会自动处理差异：
云端同步执行，自托管服务器则作为任务运行，由工具轮询至完成。

在云端使用时，Extract 以及所有 LLM 相关选项（`summary` 格式、
基于提示词或 JSON Schema 的提取、搜索的 `answer` / `summarizeResults`）
都需要付费套餐。

## 说明

- **积分。** 每页一个积分。爬取 100 个页面消耗 100 个积分。
  在 Search 中开启 `scrapeResults` 会为每条结果消耗一个积分。
- **长时间爬取。** Crawl 默认等待结果。若约四分钟后任务仍在运行，
  则返回任务 ID 和已收集的页面，不会丢失数据。之后可用 Crawl Status 工具查询。
- **Agent 使用。** 应由模型从用户问题中推断的参数（URL、查询词、输出格式、
  时间筛选、语言、来源、类别）会暴露给模型；消耗积分或属于环境配置的参数
  则由使用者在节点上设定。
- **Search 中的域名限定。** 没有 `includeDomains` 参数，请在查询词中使用
  `site:` 操作符，例如 `site:docs.python.org asyncio`。
- **Crawl 的路径过滤。** 与部分其他爬虫不同，fastCRW 的爬取接口没有
  `includePaths` / `excludePaths`。请先用 Map 列出 URL，在工作流中筛选，
  再对需要的 URL 使用 Scrape。

## 链接

- [fastCRW](https://fastcrw.com)
- [fastCRW 引擎（GitHub）](https://github.com/us/crw)
- [API 文档](https://docs.fastcrw.com)
