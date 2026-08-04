from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, as_int


class MapTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        for key in ("maxDepth", "limit", "timeout"):
            value = as_int(tool_parameters, key)
            if value is not None:
                payload[key] = value
        for key in ("useSitemap", "crawlFallback", "ignoreQueryParameters"):
            if tool_parameters.get(key) is not None:
                payload[key] = tool_parameters[key]

        result = client.map(url=tool_parameters["url"], **payload)

        links = (result.get("data") or {}).get("links") or []
        preview = "\n".join(links[:50])
        more = f"\n... and {len(links) - 50} more" if len(links) > 50 else ""
        yield self.create_text_message(f"Found {len(links)} URLs:\n{preview}{more}")

        yield self.create_json_message(result)

        yield self.create_variable_message("links", links)
        yield self.create_variable_message("count", len(links))
