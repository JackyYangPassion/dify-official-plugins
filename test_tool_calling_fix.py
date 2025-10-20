#!/usr/bin/env python3
"""
测试脚本：验证 Company Gateway 插件的工具调用修复
"""

def simulate_streaming_tool_call():
    """模拟流式响应中的工具调用处理"""
    
    # 模拟从日志中看到的流式响应数据
    streaming_chunks = [
        # Chunk 31: 工具调用开始
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': 'call_6fa41641d51d411eb271cd', 
                        'type': 'function', 
                        'function': {
                            'name': 'hugegraph_gremlin', 
                            'arguments': '{"grem'
                        }
                    }]
                }
            }]
        },
        # Chunk 32-38: 参数继续
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': 'lin_query'
                        }
                    }]
                }
            }]
        },
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': '":"g.V'
                        }
                    }]
                }
            }]
        },
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': '().limit('
                        }
                    }]
                }
            }]
        },
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': '10).value'
                        }
                    }]
                }
            }]
        },
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': 'Map(true'
                        }
                    }]
                }
            }]
        },
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': ')"'
                        }
                    }]
                }
            }]
        },
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'index': 0, 
                        'id': '', 
                        'type': 'function', 
                        'function': {
                            'arguments': '}'
                        }
                    }]
                }
            }]
        },
        # Chunk 39: 结束
        {
            'choices': [{
                'delta': {
                    'tool_calls': [{
                        'function': {'arguments': None}, 
                        'index': 0, 
                        'id': '', 
                        'type': 'function'
                    }]
                }
            }]
        },
        # Chunk 40: finish_reason
        {
            'choices': [{
                'delta': {},
                'finish_reason': 'tool_calls'
            }]
        }
    ]
    
    # 模拟我们的新逻辑
    tool_calls_dict = {}
    
    for chunk_count, chunk_data in enumerate(streaming_chunks, 1):
        choice = chunk_data['choices'][0]
        delta = choice.get('delta', {})
        finish_reason = choice.get('finish_reason')
        
        if 'tool_calls' in delta and delta['tool_calls']:
            print(f"Chunk {chunk_count}: Found tool_calls: {delta['tool_calls']}")
            
            # 处理每个工具调用
            for tool_call_data in delta['tool_calls']:
                tool_call_id = tool_call_data.get('id', '')
                function_data = tool_call_data.get('function', {})
                
                if tool_call_id:
                    # 新的工具调用
                    if tool_call_id not in tool_calls_dict:
                        tool_calls_dict[tool_call_id] = {
                            'id': tool_call_id,
                            'type': tool_call_data.get('type', 'function'),
                            'function': {
                                'name': function_data.get('name', ''),
                                'arguments': function_data.get('arguments', '') or '',
                            }
                        }
                        print(f"  -> New tool call: {function_data.get('name', '')} (id: {tool_call_id})")
                    else:
                        # 更新现有工具调用
                        additional_args = function_data.get('arguments', '') or ''
                        if additional_args:
                            tool_calls_dict[tool_call_id]['function']['arguments'] += additional_args
                            print(f"  -> Updated tool call {tool_call_id} with: '{additional_args}'")
                else:
                    # 无ID的工具调用，追加到最后一个
                    if tool_calls_dict:
                        last_tool_call_id = list(tool_calls_dict.keys())[-1]
                        additional_args = function_data.get('arguments', '') or ''
                        if additional_args:
                            tool_calls_dict[last_tool_call_id]['function']['arguments'] += additional_args
                            print(f"  -> Appended to {last_tool_call_id}: '{additional_args}'")
        
        if finish_reason:
            print(f"Chunk {chunk_count}: finish_reason = {finish_reason}")
            if finish_reason == 'tool_calls':
                print("=== FINAL TOOL CALLS ===")
                for i, (tool_id, tool_call) in enumerate(tool_calls_dict.items(), 1):
                    print(f"Tool call {i}: {tool_call['function']['name']} (id: {tool_id})")
                    print(f"  Arguments: {tool_call['function']['arguments']}")
                break
    
    return tool_calls_dict

if __name__ == "__main__":
    print("Testing tool calling fix...")
    result = simulate_streaming_tool_call()
    
    print("\n=== EXPECTED RESULT ===")
    print("Should have 1 tool call:")
    print("- hugegraph_gremlin")
    print('- Arguments: {"gremlin_query":"g.V().limit(10).valueMap(true)"}')
    
    print(f"\n=== ACTUAL RESULT ===")
    print(f"Got {len(result)} tool calls:")
    for tool_id, tool_call in result.items():
        print(f"- {tool_call['function']['name']} (id: {tool_id})")
        print(f"  Arguments: {tool_call['function']['arguments']}")
