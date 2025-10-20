from typing import Any
import requests

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class HugeGraphQueryProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        host = credentials.get("HOST")
        port = credentials.get("PORT")
        graph = credentials.get("GRAPH")
        username = credentials.get("USERNAME")
        password = credentials.get("PASSWORD")

        if not all([host, port, graph]):
            raise ToolProviderCredentialValidationError("Host, port, and graph name must be provided.")

        # Test connection to HugeGraph
        try:
            base_url = f"http://{host}:{port}"
            session = requests.Session()

            if username and password:
                session.auth = (username, password)

            # Test connectivity by getting graph info
            response = session.get(f"{base_url}/graphs/{graph}")
            response.raise_for_status()

        except Exception as e:
            raise ToolProviderCredentialValidationError(f"HugeGraph credential validation failed: {e}")