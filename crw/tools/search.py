from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient


class SearchTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {
            "limit": tool_parameters.get("limit", 5),
        }
        if tool_parameters.get("lang"):
            payload["lang"] = tool_parameters["lang"]
        if tool_parameters.get("tbs"):
            payload["tbs"] = tool_parameters["tbs"]
        if tool_parameters.get("scrapeResults"):
            payload["scrapeOptions"] = {"formats": ["markdown"]}

        payload = {k: v for k, v in payload.items() if v is not None}

        result = client.search(query=tool_parameters["query"], **payload)

        data = result.get("data", [])
        if isinstance(data, list):
            lines = []
            for r in data:
                title = r.get("title", "Untitled")
                url = r.get("url", "")
                desc = r.get("description", "")
                lines.append(f"## {title}\n{url}\n{desc}")
                if r.get("markdown"):
                    lines.append(r["markdown"])
            yield self.create_text_message(
                "\n\n---\n\n".join(lines) if lines else "No results found."
            )

        yield self.create_json_message(result)
