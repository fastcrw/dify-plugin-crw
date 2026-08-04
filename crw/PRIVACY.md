# Privacy Policy

## What this plugin does

The fastCRW plugin sends the inputs you give it (a URL, a search query, a list of
URLs, and any options you set) to the fastCRW API, and returns the response to
your Dify workflow. It does not process or store data anywhere else.

## What is collected

The plugin itself stores nothing. It keeps no database, writes no files, and
keeps no logs. Your API key is held in memory only for the duration of a single
tool call and is never written to a log or included in any output message.

Data that leaves your Dify instance:

| Data | Sent to | Why |
|---|---|---|
| The URL, query or URL list you provide | the configured CRW server | to perform the request |
| The options you set (formats, selectors, headers, schema, prompt) | the configured CRW server | to shape the request |
| Your API key | the configured CRW server | authentication |

By default the configured server is the managed fastCRW cloud at
`https://fastcrw.com/api`. If you set a Base URL, everything above goes to that
server instead and nothing is sent to fastcrw.com.

## Third parties

The plugin contacts exactly one host: the CRW server you configured. It does not
call analytics, telemetry or any other third-party service.

When you use the managed cloud, fastCRW fetches the web pages you asked for, and
those target websites see a request from fastCRW's infrastructure. Features that
are explicitly LLM-backed (the `summary` format, structured extraction with a
prompt or JSON Schema, the Extract tool, and search `answer` /
`summarizeResults`) send the fetched page content to fastCRW's managed language
model provider in order to produce the requested output. Every other feature is
plain fetching and text processing.

Handling of that data by the managed service is governed by the fastCRW privacy
policy and terms at https://fastcrw.com/privacy and https://fastcrw.com/terms,
which also describe the optional Zero Data Retention setting.

If you self-host the CRW server, no data reaches fastCRW at all.

## Children

This plugin is a developer tool and is not directed at children.

## Contact

hello@fastcrw.com
