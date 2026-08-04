from collections.abc import Generator
from typing import Any

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
            yield self.create_text_message(
                f"Crawl {job_id}: {result.get('status', 'unknown')} "
                f"({result.get('completed', 0)}/{result.get('total', 0)} pages)"
            )

        yield self.create_json_message(result)

        yield self.create_variable_message("jobId", job_id)
        yield self.create_variable_message("status", result.get("status") or "unknown")
        yield self.create_variable_message("pages", result.get("data") or [])
        yield self.create_variable_message("total", result.get("total", 0))
        yield self.create_variable_message("completed", result.get("completed", 0))
