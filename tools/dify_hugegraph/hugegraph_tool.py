import json
import requests
from typing import Any, Dict, List, Optional, Union
from dify_plugin import Tool


class HugeGraphTool(Tool):
    """HugeGraph integration tool for Dify"""

    def __init__(self):
        self.host = None
        self.port = None
        self.graph = None
        self.auth = None
        self.session = requests.Session()

    def _get_runtime_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "host",
                "type": "string",
                "required": True,
                "description": "HugeGraph server host",
                "default": "localhost"
            },
            {
                "name": "port",
                "type": "number",
                "required": True,
                "description": "HugeGraph server port",
                "default": 8080
            },
            {
                "name": "graph",
                "type": "string",
                "required": True,
                "description": "Graph name",
                "default": "hugegraph"
            },
            {
                "name": "username",
                "type": "string",
                "required": False,
                "description": "Username for authentication"
            },
            {
                "name": "password",
                "type": "string",
                "required": False,
                "description": "Password for authentication"
            }
        ]

    def _setup_connection(self, parameters: Dict[str, Any]) -> None:
        """Setup connection to HugeGraph server"""
        self.host = parameters.get('host', 'localhost')
        self.port = parameters.get('port', 8080)
        self.graph = parameters.get('graph', 'hugegraph')

        username = parameters.get('username')
        password = parameters.get('password')
        if username and password:
            self.auth = (username, password)
            self.session.auth = self.auth

    def _get_base_url(self) -> str:
        """Get base URL for HugeGraph REST API"""
        return f"http://{self.host}:{self.port}/graphs/{self.graph}"

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to HugeGraph API"""
        url = f"{self._get_base_url()}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    def add_vertex(self, parameters: Dict[str, Any]) -> str:
        """Add a vertex to the graph"""
        self._setup_connection(parameters)

        label = parameters.get('label')
        properties = parameters.get('properties', {})
        vertex_id = parameters.get('id')

        if not label:
            return "Error: Vertex label is required"

        vertex_data = {
            "label": label,
            "properties": properties
        }

        if vertex_id:
            vertex_data["id"] = vertex_id

        result = self._make_request('POST', '/graph/vertices', vertex_data)

        if "error" in result:
            return f"Failed to add vertex: {result['error']}"

        return f"Successfully added vertex: {json.dumps(result, indent=2)}"

    def get_vertex(self, parameters: Dict[str, Any]) -> str:
        """Get a vertex by ID"""
        self._setup_connection(parameters)

        vertex_id = parameters.get('id')
        if not vertex_id:
            return "Error: Vertex ID is required"

        result = self._make_request('GET', f'/graph/vertices/{vertex_id}')

        if "error" in result:
            return f"Failed to get vertex: {result['error']}"

        return f"Vertex details: {json.dumps(result, indent=2)}"

    def add_edge(self, parameters: Dict[str, Any]) -> str:
        """Add an edge between two vertices"""
        self._setup_connection(parameters)

        label = parameters.get('label')
        source_id = parameters.get('source_id')
        target_id = parameters.get('target_id')
        properties = parameters.get('properties', {})
        edge_id = parameters.get('id')

        if not all([label, source_id, target_id]):
            return "Error: Edge label, source_id, and target_id are required"

        edge_data = {
            "label": label,
            "outV": source_id,
            "inV": target_id,
            "properties": properties
        }

        if edge_id:
            edge_data["id"] = edge_id

        result = self._make_request('POST', '/graph/edges', edge_data)

        if "error" in result:
            return f"Failed to add edge: {result['error']}"

        return f"Successfully added edge: {json.dumps(result, indent=2)}"

    def get_edge(self, parameters: Dict[str, Any]) -> str:
        """Get an edge by ID"""
        self._setup_connection(parameters)

        edge_id = parameters.get('id')
        if not edge_id:
            return "Error: Edge ID is required"

        result = self._make_request('GET', f'/graph/edges/{edge_id}')

        if "error" in result:
            return f"Failed to get edge: {result['error']}"

        return f"Edge details: {json.dumps(result, indent=2)}"

    def gremlin_query(self, parameters: Dict[str, Any]) -> str:
        """Execute Gremlin query"""
        self._setup_connection(parameters)

        gremlin = parameters.get('gremlin')
        if not gremlin:
            return "Error: Gremlin query is required"

        query_data = {
            "gremlin": gremlin,
            "language": "gremlin-groovy"
        }

        result = self._make_request('POST', '/gremlin', query_data)

        if "error" in result:
            return f"Failed to execute Gremlin query: {result['error']}"

        return f"Query result: {json.dumps(result, indent=2)}"

    def cypher_query(self, parameters: Dict[str, Any]) -> str:
        """Execute Cypher query"""
        self._setup_connection(parameters)

        cypher = parameters.get('cypher')
        if not cypher:
            return "Error: Cypher query is required"

        query_data = {
            "cypher": cypher
        }

        result = self._make_request('POST', '/cypher', query_data)

        if "error" in result:
            return f"Failed to execute Cypher query: {result['error']}"

        return f"Query result: {json.dumps(result, indent=2)}"

    def list_vertices(self, parameters: Dict[str, Any]) -> str:
        """List vertices with optional label filter"""
        self._setup_connection(parameters)

        label = parameters.get('label')
        limit = parameters.get('limit', 100)

        query_params = {"limit": limit}
        if label:
            query_params["label"] = label

        result = self._make_request('GET', '/graph/vertices', query_params)

        if "error" in result:
            return f"Failed to list vertices: {result['error']}"

        return f"Vertices: {json.dumps(result, indent=2)}"

    def list_edges(self, parameters: Dict[str, Any]) -> str:
        """List edges with optional label filter"""
        self._setup_connection(parameters)

        label = parameters.get('label')
        limit = parameters.get('limit', 100)

        query_params = {"limit": limit}
        if label:
            query_params["label"] = label

        result = self._make_request('GET', '/graph/edges', query_params)

        if "error" in result:
            return f"Failed to list edges: {result['error']}"

        return f"Edges: {json.dumps(result, indent=2)}"

    def delete_vertex(self, parameters: Dict[str, Any]) -> str:
        """Delete a vertex by ID"""
        self._setup_connection(parameters)

        vertex_id = parameters.get('id')
        if not vertex_id:
            return "Error: Vertex ID is required"

        result = self._make_request('DELETE', f'/graph/vertices/{vertex_id}')

        if "error" in result:
            return f"Failed to delete vertex: {result['error']}"

        return f"Successfully deleted vertex {vertex_id}"

    def delete_edge(self, parameters: Dict[str, Any]) -> str:
        """Delete an edge by ID"""
        self._setup_connection(parameters)

        edge_id = parameters.get('id')
        if not edge_id:
            return "Error: Edge ID is required"

        result = self._make_request('DELETE', f'/graph/edges/{edge_id}')

        if "error" in result:
            return f"Failed to delete edge: {result['error']}"

        return f"Successfully deleted edge {edge_id}"

    def get_schema(self, parameters: Dict[str, Any]) -> str:
        """Get graph schema information"""
        self._setup_connection(parameters)

        result = self._make_request('GET', '/schema')

        if "error" in result:
            return f"Failed to get schema: {result['error']}"

        return f"Schema: {json.dumps(result, indent=2)}"