from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient


class CrawlStatusTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        job_id = tool_parameters["job_id"]
        action = tool_parameters.get("action", "status")

        if action == "cancel":
            result = client.cancel_crawl(job_id)
            yield self.create_text_message(f"Crawl job {job_id} cancelled.")
        else:
            result = client.crawl_status(job_id)
            status = result.get("status", "unknown")
            total = result.get("total", 0)
            completed = result.get("completed", 0)
            yield self.create_text_message(
                f"Crawl {job_id}: {status} ({completed}/{total} pages)"
            )

        yield self.create_json_message(result)
