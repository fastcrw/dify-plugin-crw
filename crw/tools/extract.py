import time
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, get_array_params, get_json_params

# Whole-tool ceiling shared by the POST and any follow-up polling, kept under
# Dify's 300s invocation limit.
EXTRACT_TOTAL_BUDGET = 280.0


class ExtractTool(Tool):
    """Structured extraction across several URLs.

    The managed API runs this synchronously and answers with `results`. A
    self-hosted engine answers with a job `id` instead, so poll that. The user
    should not have to know which backend they are on.
    """

    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        urls = get_array_params(tool_parameters, "urls")
        if not urls:
            raise ValueError("At least one URL is required.")

        payload: dict[str, Any] = {}
        if tool_parameters.get("prompt"):
            payload["prompt"] = tool_parameters["prompt"]
        schema = get_json_params(tool_parameters, "schema")
        if schema:
            payload["schema"] = schema
        if not payload:
            # The API requires one of them; say so here rather than spending a
            # round trip to relay its 400.
            raise ValueError(
                "Provide an Extraction Prompt, a JSON Schema, or both, "
                "so the extractor knows what to look for."
            )

        started = time.monotonic()
        result = client.extract(urls, **payload)

        if result.get("id") and "results" not in result:
            # The POST itself may already have eaten most of the invocation
            # budget, so give the poll only what is left of a shared ceiling.
            # Adding a fresh 240s on top of a slow 270s POST would blow past
            # Dify's 300s limit and lose the job id we are polling for.
            remaining = EXTRACT_TOTAL_BUDGET - (time.monotonic() - started)
            if remaining > 0:
                result = client.poll(
                    client.extract_status, result["id"], budget=remaining
                )

        results = result.get("results") or []
        yield self.create_json_message(result)

        lines = []
        for item in results:
            if item.get("data") is not None:
                lines.append(f"{item.get('url', '')}\n{item['data']}")
            elif item.get("error"):
                lines.append(f"{item.get('url', '')}\nfailed: {item['error']}")
        yield self.create_text_message(
            "\n\n".join(lines) if lines else "No data extracted."
        )

        yield self.create_variable_message("results", results)
        yield self.create_variable_message(
            "data",
            [item.get("data") for item in results if item.get("data") is not None],
        )
        yield self.create_variable_message(
            "status", result.get("status") or "completed"
        )
        yield self.create_variable_message("jobId", result.get("id") or "")
