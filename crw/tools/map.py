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
            f"Found {len(links)} URLs:\n"
            + "\n".join(links[:50])
            + (f"\n... and {len(links) - 50} more" if len(links) > 50 else "")
        )
        yield self.create_json_message(result)
