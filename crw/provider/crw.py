from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.crw_client import CrwClient


class CrwProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            client = CrwClient(
                api_key=credentials["api_key"],
                base_url=credentials.get("base_url"),
            )
            client.scrape(url="https://example.com", formats=["markdown"])
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
