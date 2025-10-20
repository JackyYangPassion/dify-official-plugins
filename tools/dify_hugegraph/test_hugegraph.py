#!/usr/bin/env python3
"""
Simple test script for HugeGraph Dify Tool Plugin
"""

import json
from hugegraph_tool import HugeGraphTool


def test_hugegraph_tool():
    """Test basic functionality of HugeGraph tool"""

    tool = HugeGraphTool()

    # Test parameters
    test_params = {
        'host': 'localhost',
        'port': 8080,
        'graph': 'hugegraph',
        # 'username': 'admin',
        # 'password': 'admin'
    }

    print("=== Testing HugeGraph Dify Tool Plugin ===\n")

    # Test 1: Get schema (should work even if HugeGraph is not running)
    print("1. Testing get_schema...")
    try:
        result = tool.get_schema(test_params)
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Test 2: Add vertex
    print("2. Testing add_vertex...")
    try:
        vertex_params = test_params.copy()
        vertex_params.update({
            'label': 'person',
            'properties': {'name': 'Alice', 'age': 30}
        })
        result = tool.add_vertex(vertex_params)
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Test 3: List vertices
    print("3. Testing list_vertices...")
    try:
        list_params = test_params.copy()
        list_params.update({'limit': 10})
        result = tool.list_vertices(list_params)
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Test 4: Gremlin query
    print("4. Testing gremlin_query...")
    try:
        gremlin_params = test_params.copy()
        gremlin_params.update({'gremlin': 'g.V().limit(5)'})
        result = tool.gremlin_query(gremlin_params)
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    print("=== Test completed ===")


if __name__ == "__main__":
    test_hugegraph_tool()