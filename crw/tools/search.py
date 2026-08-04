from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, as_int, get_array_params


def _flatten(data: Any) -> list[dict[str, Any]]:
    """Three envelopes are in play and all of them are real:

    * managed API: `data` is a flat list
    * `sources` set: `data` is `{web, news, images}`
    * self-hosted engine: `data` is `{results, answer, citations}`, where
      `results` is itself either of the two above

    Iterative rather than recursive: `base_url` is user-configurable, and a
    self-hosted server answering with deeply nested `results` would otherwise
    raise RecursionError, the one failure this module cannot wrap.
    """
    for _ in range(8):
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        if "results" in data:
            data = data["results"]
            continue
        out: list[dict[str, Any]] = []
        for key in ("web", "news", "images"):
            out.extend(data.get(key) or [])
        return out
    return []


def _answer(result: dict[str, Any]) -> str:
    """Managed puts `answer` at the top level; the engine nests it under `data`."""
    if result.get("answer"):
        return str(result["answer"])
    data = result.get("data")
    if isinstance(data, dict) and data.get("answer"):
        return str(data["answer"])
    return ""


class SearchTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        limit = as_int(tool_parameters, "limit")
        if limit is not None:
            payload["limit"] = limit
        for key in ("lang", "tbs"):
            if tool_parameters.get(key):
                payload[key] = tool_parameters[key]
        for key in ("sources", "categories"):
            values = get_array_params(tool_parameters, key)
            if values:
                payload[key] = values

        answer = bool(tool_parameters.get("answer"))
        summarize = bool(tool_parameters.get("summarizeResults"))
        scrape = bool(tool_parameters.get("scrapeResults"))

        if scrape or answer or summarize:
            # The API rejects answer/summarizeResults unless the scrape produces
            # markdown, so it is not a user-facing choice.
            payload["scrapeOptions"] = {"formats": ["markdown"]}
        if answer:
            payload["answer"] = True
        if summarize:
            payload["summarizeResults"] = True

        result = client.search(query=tool_parameters["query"], **payload)

        results = _flatten(result.get("data"))
        answer_text = _answer(result)

        lines = []
        if answer_text:
            lines.append(answer_text)
        for item in results:
            lines.append(
                f"## {item.get('title', 'Untitled')}\n"
                f"{item.get('url', '')}\n{item.get('description', '')}"
            )
            if item.get("summary"):
                lines.append(item["summary"])
            elif item.get("markdown"):
                lines.append(item["markdown"])
        yield self.create_text_message(
            "\n\n---\n\n".join(lines) if lines else "No results found."
        )

        yield self.create_json_message(result)

        yield self.create_variable_message("results", results)
        yield self.create_variable_message("answer", answer_text)
        yield self.create_variable_message("urls", [r.get("url", "") for r in results])
        yield self.create_variable_message("count", len(results))
