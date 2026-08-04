from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, as_int, get_array_params


class CrawlTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        for key in ("maxDepth", "maxPages", "waitFor"):
            value = as_int(tool_parameters, key)
            if value is not None:
                payload[key] = value
        if tool_parameters.get("onlyMainContent") is not None:
            payload["onlyMainContent"] = tool_parameters["onlyMainContent"]
        if tool_parameters.get("renderJs") is not None:
            payload["renderJs"] = tool_parameters["renderJs"]
        formats = get_array_params(tool_parameters, "formats")
        if formats:
            payload["formats"] = formats

        result = client.crawl(url=tool_parameters["url"], **payload)
        job_id = result.get("id", "")

        if tool_parameters.get("wait_for_results", True) and job_id:
            result = client.poll(client.crawl_status, job_id)

        yield self.create_json_message(result)

        status = result.get("status", "processing")
        pages = result.get("data") or []
        # Test against the TERMINAL set, not one in-progress string. The API
        # answers `accepted` right after the POST and `scraping` while running,
        # never `processing`, so matching on "processing" made this branch dead
        # in exactly the long-crawl case it exists for.
        if status == "completed":
            yield self.create_text_message(
                f"Crawl completed: {result.get('completed', 0)}/{result.get('total', 0)} pages scraped."
            )
        elif status not in ("failed", "cancelled") and job_id:
            # Deliberately not an error: the job is still running server-side and
            # the id is the only way back to it.
            yield self.create_text_message(
                f"Crawl still running after the wait limit. Job ID: {job_id}. "
                f"{len(pages)} pages collected so far. Poll it with the Crawl Status tool."
            )
        else:
            yield self.create_text_message(f"Crawl {status}. Job ID: {job_id}")

        yield self.create_variable_message("jobId", job_id)
        yield self.create_variable_message("status", status)
        yield self.create_variable_message("pages", pages)
        yield self.create_variable_message("total", result.get("total", 0))
        yield self.create_variable_message("completed", result.get("completed", 0))
