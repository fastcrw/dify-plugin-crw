from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .crw_client import CrwClient, get_array_params, get_json_params


class ScrapeTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        client = CrwClient(
            api_key=self.runtime.credentials["api_key"],
            base_url=self.runtime.credentials.get("base_url"),
        )

        payload: dict[str, Any] = {}
        payload["formats"] = get_array_params(tool_parameters, "formats") or [
            "markdown"
        ]
        payload["onlyMainContent"] = tool_parameters.get("onlyMainContent", True)

        # Optional parameters — only include if set
        if tool_parameters.get("renderJs") is not None:
            payload["renderJs"] = tool_parameters["renderJs"]
        if tool_parameters.get("waitFor"):
            payload["waitFor"] = tool_parameters["waitFor"]
        if tool_parameters.get("cssSelector"):
            payload["cssSelector"] = tool_parameters["cssSelector"]
        if tool_parameters.get("xpath"):
            payload["xpath"] = tool_parameters["xpath"]
        if tool_parameters.get("stealth") is not None:
            payload["stealth"] = tool_parameters["stealth"]
        if tool_parameters.get("proxy"):
            payload["proxy"] = tool_parameters["proxy"]

        include_tags = get_array_params(tool_parameters, "includeTags")
        if include_tags:
            payload["includeTags"] = include_tags
        exclude_tags = get_array_params(tool_parameters, "excludeTags")
        if exclude_tags:
            payload["excludeTags"] = exclude_tags

        headers = get_json_params(tool_parameters, "headers")
        if headers:
            payload["headers"] = headers

        json_schema = get_json_params(tool_parameters, "jsonSchema")
        if json_schema:
            payload["jsonSchema"] = json_schema
            if "json" not in payload["formats"]:
                payload["formats"].append("json")

        # Clean None values
        payload = {k: v for k, v in payload.items() if v is not None}

        result = client.scrape(url=tool_parameters["url"], **payload)

        # Yield markdown as text for direct display in chat
        data = result.get("data", {})
        markdown = data.get("markdown", "")
        if markdown:
            yield self.create_text_message(markdown)

        # Yield full response as JSON for workflow consumption
        yield self.create_json_message(result)
