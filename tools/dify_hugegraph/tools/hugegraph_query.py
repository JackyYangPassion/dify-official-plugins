from collections.abc import Generator
from typing import Any
import requests
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class HugeGraphQueryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        # Access credentials from provider config
        host = self.runtime.credentials.get("HOST")
        port = self.runtime.credentials.get("PORT")
        graph = self.runtime.credentials.get("GRAPH")
        username = self.runtime.credentials.get("USERNAME")
        password = self.runtime.credentials.get("PASSWORD")

        operation = tool_parameters.get("operation")

        if not all([host, port, graph, operation]):
            yield self.create_text_message("Missing required parameters: host, port, graph, or operation.")
            return

        try:
            base_url = f"http://{host}:{port}"
            session = requests.Session()

            if username and password:
                session.auth = (username, password)

            result = self._execute_operation(session, base_url, graph, operation, tool_parameters)

            if isinstance(result, dict) and "error" in result:
                yield self.create_text_message(f"Error: {result['error']}")
            else:
                yield self.create_json_message(result)
                yield self.create_text_message(json.dumps(result, indent=2, ensure_ascii=False))

        except Exception as e:
            yield self.create_text_message(f"Error executing HugeGraph operation: {str(e)}")

    def _execute_operation(self, session: requests.Session, base_url: str, graph: str, operation: str, params: dict) -> dict:
        """Execute the specified HugeGraph operation"""

        if operation == "gremlin_query":
            return self._gremlin_query(session, base_url, graph, params)
        elif operation == "cypher_query":
            return self._cypher_query(session, base_url, graph, params)
        elif operation == "add_vertex":
            return self._add_vertex(session, base_url, graph, params)
        elif operation == "get_vertex":
            return self._get_vertex(session, base_url, graph, params)
        elif operation == "add_edge":
            return self._add_edge(session, base_url, graph, params)
        elif operation == "get_edge":
            return self._get_edge(session, base_url, graph, params)
        elif operation == "list_vertices":
            return self._list_vertices(session, base_url, graph, params)
        elif operation == "list_edges":
            return self._list_edges(session, base_url, graph, params)
        elif operation == "get_schema":
            return self._get_schema(session, base_url, graph, params)
        elif operation == "delete_vertex":
            return self._delete_vertex(session, base_url, graph, params)
        elif operation == "delete_edge":
            return self._delete_edge(session, base_url, graph, params)
        else:
            return {"error": f"Unsupported operation: {operation}"}

    def _gremlin_query(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Execute Gremlin query"""
        gremlin = params.get("query")
        if not gremlin:
            return {"error": "Gremlin query is required"}

        query_data = {
            "gremlin": gremlin,
            "language": "gremlin-groovy"
        }

        response = session.post(f"{base_url}/graphs/{graph}/gremlin", json=query_data)
        response.raise_for_status()
        return response.json()

    def _cypher_query(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Execute Cypher query"""
        cypher = params.get("query")
        if not cypher:
            return {"error": "Cypher query is required"}

        query_data = {"cypher": cypher}

        response = session.post(f"{base_url}/graphs/{graph}/cypher", json=query_data)
        response.raise_for_status()
        return response.json()

    def _add_vertex(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Add a vertex to the graph"""
        label = params.get("label")
        properties_str = params.get("properties", "{}")
        vertex_id = params.get("vertex_id")

        if not label:
            return {"error": "Vertex label is required"}

        # Parse properties JSON string
        try:
            properties = json.loads(properties_str) if isinstance(properties_str, str) else properties_str
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for properties"}

        vertex_data = {
            "label": label,
            "properties": properties
        }

        if vertex_id:
            vertex_data["id"] = vertex_id

        response = session.post(f"{base_url}/graphs/{graph}/graph/vertices", json=vertex_data)
        response.raise_for_status()
        return response.json()

    def _get_vertex(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Get a vertex by ID"""
        vertex_id = params.get("vertex_id")
        if not vertex_id:
            return {"error": "Vertex ID is required"}

        response = session.get(f"{base_url}/graphs/{graph}/graph/vertices/{vertex_id}")
        response.raise_for_status()
        return response.json()

    def _add_edge(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Add an edge between two vertices"""
        label = params.get("label")
        source_id = params.get("source_id")
        target_id = params.get("target_id")
        properties_str = params.get("properties", "{}")
        edge_id = params.get("edge_id")

        if not all([label, source_id, target_id]):
            return {"error": "Edge label, source_id, and target_id are required"}

        # Parse properties JSON string
        try:
            properties = json.loads(properties_str) if isinstance(properties_str, str) else properties_str
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for properties"}

        edge_data = {
            "label": label,
            "outV": source_id,
            "inV": target_id,
            "properties": properties
        }

        if edge_id:
            edge_data["id"] = edge_id

        response = session.post(f"{base_url}/graphs/{graph}/graph/edges", json=edge_data)
        response.raise_for_status()
        return response.json()

    def _get_edge(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Get an edge by ID"""
        edge_id = params.get("edge_id")
        if not edge_id:
            return {"error": "Edge ID is required"}

        response = session.get(f"{base_url}/graphs/{graph}/graph/edges/{edge_id}")
        response.raise_for_status()
        return response.json()

    def _list_vertices(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """List vertices with optional label filter"""
        label = params.get("label")
        limit = params.get("limit", 100)

        query_params = {"limit": limit}
        if label:
            query_params["label"] = label

        response = session.get(f"{base_url}/graphs/{graph}/graph/vertices", params=query_params)
        response.raise_for_status()
        return response.json()

    def _list_edges(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """List edges with optional label filter"""
        label = params.get("label")
        limit = params.get("limit", 100)

        query_params = {"limit": limit}
        if label:
            query_params["label"] = label

        response = session.get(f"{base_url}/graphs/{graph}/graph/edges", params=query_params)
        response.raise_for_status()
        return response.json()

    def _delete_vertex(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Delete a vertex by ID"""
        vertex_id = params.get("vertex_id")
        if not vertex_id:
            return {"error": "Vertex ID is required"}

        response = session.delete(f"{base_url}/graphs/{graph}/graph/vertices/{vertex_id}")
        response.raise_for_status()
        return {"message": f"Successfully deleted vertex {vertex_id}"}

    def _delete_edge(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Delete an edge by ID"""
        edge_id = params.get("edge_id")
        if not edge_id:
            return {"error": "Edge ID is required"}

        response = session.delete(f"{base_url}/graphs/{graph}/graph/edges/{edge_id}")
        response.raise_for_status()
        return {"message": f"Successfully deleted edge {edge_id}"}

    def _get_schema(self, session: requests.Session, base_url: str, graph: str, params: dict) -> dict:
        """Get graph schema information"""
        response = session.get(f"{base_url}/graphs/{graph}/schema")
        response.raise_for_status()
        return response.json()