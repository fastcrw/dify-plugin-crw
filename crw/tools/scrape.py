from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, as_int, get_array_params, get_json_params


class ScrapeTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {
            "formats": get_array_params(tool_parameters, "formats") or ["markdown"],
            "onlyMainContent": tool_parameters.get("onlyMainContent", True),
        }

        if tool_parameters.get("renderJs") is not None:
            payload["renderJs"] = tool_parameters["renderJs"]
        for key in ("cssSelector", "country"):
            if tool_parameters.get(key):
                payload[key] = tool_parameters[key]

        wait_for = as_int(tool_parameters, "waitFor")
        if wait_for is not None:
            payload["waitFor"] = wait_for

        timeout_ms = as_int(tool_parameters, "timeout")
        if timeout_ms is not None:
            payload["deadlineMs"] = timeout_ms

        for key in ("includeTags", "excludeTags"):
            tags = get_array_params(tool_parameters, key)
            if tags:
                payload[key] = tags

        headers = get_json_params(tool_parameters, "headers")
        if headers:
            payload["headers"] = headers

        # Structured extraction. A schema and a bare prompt both only take effect
        # when the `json` format is requested, so request it on the user's behalf.
        json_schema = get_json_params(tool_parameters, "jsonSchema")
        if json_schema:
            payload["jsonSchema"] = json_schema
        prompt = tool_parameters.get("prompt")
        if prompt:
            payload["extract"] = {"prompt": prompt}
        if (json_schema or prompt) and "json" not in payload["formats"]:
            payload["formats"].append("json")

        result = client.scrape(url=tool_parameters["url"], **payload)

        data = result.get("data") or {}
        markdown = data.get("markdown") or ""
        if markdown:
            yield self.create_text_message(markdown)

        yield self.create_json_message(result)

        metadata = data.get("metadata") or {}
        yield self.create_variable_message("markdown", markdown)
        yield self.create_variable_message("html", data.get("html") or "")
        yield self.create_variable_message("links", data.get("links") or [])
        # Named `extracted`, not `json`: Dify reserves the variable names json,
        # text and files, and emitting one fails the whole workflow node.
        # Never emit None either, for the same reason: an unrequested format
        # comes back as the empty value of its declared type.
        yield self.create_variable_message("extracted", data.get("json") or {})
        yield self.create_variable_message("summary", data.get("summary") or "")
        yield self.create_variable_message("title", metadata.get("title") or "")
        yield self.create_variable_message("sourceUrl", metadata.get("sourceURL") or "")
        yield self.create_variable_message(
            "statusCode", metadata.get("statusCode") or 0
        )
