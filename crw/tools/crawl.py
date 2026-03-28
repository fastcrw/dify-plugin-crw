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
            yield self.create_text_message(f"Crawl started. Job ID: {result['id']}")
