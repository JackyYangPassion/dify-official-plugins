import json
import logging
import time
from decimal import Decimal
from collections.abc import Generator
from typing import Optional, Union, cast, Any, List, Dict
import tiktoken
import requests

from ..common_gateway import _CommonGateway

from dify_plugin import LargeLanguageModel
from dify_plugin.entities import I18nObject
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeError,
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)
from dify_plugin.entities.model import (
    AIModelEntity,
    FetchFrom,
    ModelType,
    PriceConfig,
)
from dify_plugin.entities.model.llm import (
    LLMMode,
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageContentType,
    PromptMessageTool,
    SystemPromptMessage,
    TextPromptMessageContent,
    UserPromptMessage,
    ToolPromptMessage,
)

# 按照 Dify 文档设置日志记录器
try:
    from dify_plugin.config.logger_format import plugin_logger_handler
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not any(isinstance(handler, type(plugin_logger_handler)) for handler in logger.handlers):
        logger.addHandler(plugin_logger_handler)
except ImportError:
    # 如果导入失败，使用标准日志记录器
    logger = logging.getLogger(__name__)


class CompanyGatewayLargeLanguageModel(_CommonGateway, LargeLanguageModel):
    """
    Model class for Company Gateway large language models.
    """

    def __init__(self, model_schemas=None):
        """
        Initialize the Company Gateway LLM model
        
        :param model_schemas: list of model schemas
        """
        # Initialize parent classes
        _CommonGateway.__init__(self)
        LargeLanguageModel.__init__(self, model_schemas or [])

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        """
        Invoke large language model

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        :return: full response or stream response chunk generator result
        """
        # Configure function calling support when tools are provided
        if tools:
            # Set function calling type to enable tool calling
            credentials = credentials.copy()  # Don't modify original credentials
            credentials["function_calling_type"] = "tool_call"
            credentials["stream_function_calling"] = "support"
        
        return self._chat_generate(
            model=model,
            credentials=credentials,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            tools=tools,
            stop=stop,
            stream=stream,
            user=user,
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        """
        Get number of tokens for given prompt messages

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param tools: tools for tool calling
        :return: number of tokens
        """
        return self._num_tokens_from_messages(model, prompt_messages, tools)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            # Transform credentials to request parameters
            credentials_kwargs = self._to_credential_kwargs(credentials)
            
            # Prepare headers
            headers = self._prepare_headers(
                api_key=credentials_kwargs.get('api_key', ''),
                custom_headers=credentials_kwargs.get('custom_headers')
            )
            
            # Construct URL with model in path
            base_url = credentials_kwargs.get('base_url', 'http://xyz.cn')
            if base_url.endswith('/'):
                base_url = base_url[:-1]
            url = f"{base_url}/{model}"
            
            # Test with a simple message (model is in URL, not in body)
            test_data = {
                "messages": [{"role": "user", "content": "hello"}],
                "max_tokens": 10,
                "temperature": 0.1,
                "stream": False
            }
            
            # Make validation request
            response = self._make_request(
                method="POST",
                url=url,
                headers=headers,
                data=test_data,
                timeout=30
            )
            
            # Check if response is valid
            if response.status_code != 200:
                raise CredentialsValidateFailedError(
                    f"Validation failed with status {response.status_code}: {self._extract_error_message(response)}"
                )
                
            response_data = response.json()
            if 'choices' not in response_data:
                raise CredentialsValidateFailedError("Invalid response format from gateway")
                
        except Exception as ex:
            if isinstance(ex, CredentialsValidateFailedError):
                raise ex
            raise CredentialsValidateFailedError(str(ex))

    def _chat_generate(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        """
        Invoke llm chat model

        :param model: model name
        :param credentials: credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        :return: full response or stream response chunk generator result
        """
        logger.info(f"Starting chat generation for model: {model}")
        logger.info(f"Stream mode: {stream}")
        logger.info(f"Number of prompt messages: {len(prompt_messages)}")
        logger.info(f"Tools provided: {len(tools) if tools else 0}")
        logger.info(f"Model parameters: {model_parameters}")
        
        # Log tool information if tools are provided
        if tools:
            logger.info("Tool calling enabled - tools:")
            for i, tool in enumerate(tools):
                logger.info(f"  Tool {i+1}: {tool.name} - {tool.description}")
                logger.debug(f"  Tool {i+1} parameters: {tool.parameters}")
        
        # Transform credentials to request parameters
        credentials_kwargs = self._to_credential_kwargs(credentials)
        
        # Prepare headers
        headers = self._prepare_headers(
            api_key=credentials_kwargs.get('api_key', ''),
            custom_headers=credentials_kwargs.get('custom_headers')
        )
        
        # Construct URL with model in path
        base_url = credentials_kwargs.get('base_url', 'http://xyz.cn')
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        url = f"{base_url}/{model}"
        
        logger.info(f"Request URL: {url}")
        
        # Convert prompt messages to OpenAI format
        messages = []
        for i, msg in enumerate(prompt_messages):
            try:
                converted_msg = self._convert_prompt_message_to_dict(msg)
                messages.append(converted_msg)
                
                # 记录消息转换详情
                content = converted_msg.get('content', '')
                if isinstance(content, str):
                    content_length = len(content)
                    logger.info(f"Message {i}: role={converted_msg.get('role')}, content_length={content_length}")
                    # 对于较短的消息，记录完整内容用于调试
                    if content_length < 100:
                        logger.debug(f"Message {i} content: {content}")
                    else:
                        logger.debug(f"Message {i} content preview: {content[:50]}...")
                else:
                    logger.info(f"Message {i}: role={converted_msg.get('role')}, content_type={type(content)}")
                    
            except Exception as e:
                logger.error(f"Failed to convert message {i}: {e}")
                logger.error(f"Message type: {type(msg)}")
                logger.error(f"Message content: {getattr(msg, 'content', 'No content')}")
                raise
        
        # Prepare request data (model is in URL, not in body)
        request_data = {
            "messages": messages,
            "stream": stream,
            **model_parameters
        }
        
        # Handle response_format parameter - convert string to object format
        if "response_format" in request_data:
            response_format_value = request_data["response_format"]
            if isinstance(response_format_value, str):
                if response_format_value == "json_object":
                    request_data["response_format"] = {"type": "json_object"}
                elif response_format_value == "json_schema":
                    request_data["response_format"] = {"type": "json_schema"}
                elif response_format_value == "text":
                    request_data["response_format"] = {"type": "text"}
                else:
                    # For any other string value, keep as is but log a warning
                    logger.warning(f"Unknown response_format value: {response_format_value}, keeping as string")
            # If it's already an object, keep it as is
            logger.info(f"Final response_format: {request_data['response_format']}")
        
        # Add tools if provided
        if tools:
            request_data["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]
            # Set tool_choice to auto when tools are provided
            if "tool_choice" not in model_parameters:
                request_data["tool_choice"] = "auto"
        
        # Add stop tokens
        if stop:
            request_data["stop"] = stop
            
        # Add user if provided
        if user:
            request_data["user"] = user

        # 最终验证请求数据
        try:
            import json
            json_str = json.dumps(request_data, ensure_ascii=False)
            logger.debug(f"Final request payload size: {len(json_str.encode('utf-8'))} bytes")
            
            # 检查是否有可能导致问题的内容
            for msg in request_data.get('messages', []):
                content = msg.get('content', '')
                if isinstance(content, str) and len(content) > 0:
                    # 检查特殊字符模式
                    import re
                    special_patterns = [
                        r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',  # 控制字符
                        r'[^\x20-\x7E\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]',  # 非常见字符
                    ]
                    
                    for pattern in special_patterns:
                        if re.search(pattern, content):
                            logger.warning(f"Found potentially problematic characters in message content")
                            break
                            
        except Exception as e:
            logger.error(f"Error validating request data: {e}")

        start_time = time.time()
        
        try:
            # Make request
            logger.info(f"Making request to {url}")
            response = self._make_request(
                method="POST",
                url=url,
                headers=headers,
                data=request_data,
                stream=stream,
                timeout=120
            )
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check if response is successful
            if response.status_code != 200:
                error_msg = self._extract_error_message(response)
                logger.error(f"HTTP {response.status_code} error: {error_msg}")
                raise InvokeError(f"HTTP {response.status_code}: {error_msg}")
            
            if stream:
                logger.info("Processing stream response")
                # Check if response is actually streaming
                content_type = response.headers.get('content-type', '')
                logger.info(f"Response content-type: {content_type}")
                
                if 'text/event-stream' not in content_type and 'application/x-ndjson' not in content_type:
                    logger.warning(f"Expected streaming content-type but got: {content_type}")
                    # Try to handle as non-streaming response
                    logger.info("Attempting to handle as non-streaming response")
                    try:
                        response_data = response.json()
                        logger.info(f"Successfully parsed as JSON: {response_data.keys() if isinstance(response_data, dict) else type(response_data)}")
                        return self._handle_chat_generate_response_from_data(
                            model, credentials, response_data, prompt_messages, tools, start_time
                        )
                    except Exception as json_error:
                        logger.error(f"Failed to parse as JSON: {json_error}")
                        logger.error(f"Response text preview: {response.text[:500]}")
                        raise InvokeError(f"Invalid response format: {json_error}")
                
                return self._handle_chat_generate_stream_response(
                    model, credentials, response, prompt_messages, tools, start_time
                )
            else:
                logger.info("Processing non-stream response")
                return self._handle_chat_generate_response(
                    model, credentials, response, prompt_messages, tools, start_time
                )
                
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                # 特别处理 400 错误
                error_msg = self._extract_error_message(e.response)
                logger.error(f"400 Bad Request error: {error_msg}")
                logger.error(f"Request data summary: {len(request_data.get('messages', []))} messages, stream={stream}")
                
                # 记录可能有问题的消息内容
                for i, msg in enumerate(request_data.get('messages', [])):
                    content = msg.get('content', '')
                    if isinstance(content, str):
                        logger.error(f"Message {i} ({msg.get('role')}): length={len(content)}, preview='{content[:50]}...'")
                
                raise InvokeBadRequestError(f"Bad Request: {error_msg}")
            else:
                logger.error(f"HTTP error: {e}")
                raise InvokeError(f"HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request data keys: {list(request_data.keys())}")
            raise InvokeError(str(e))

    def _handle_chat_generate_response(
        self,
        model: str,
        credentials: dict,
        response,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
        start_time: float = 0,
    ) -> LLMResult:
        """
        Handle llm chat response

        :param model: model name
        :param credentials: credentials
        :param response: response
        :param prompt_messages: prompt messages
        :param tools: tools for tool calling
        :param start_time: request start time
        :return: llm response
        """
        try:
            response_data = response.json()
            
            if 'choices' not in response_data or not response_data['choices']:
                raise InvokeError("Invalid response: no choices found")
                
            choice = response_data['choices'][0]
            message = choice.get('message', {})
            
            # Extract content and tool calls
            content = message.get('content', '')
            tool_calls = []
            
            if 'tool_calls' in message and message['tool_calls']:
                tool_calls = self._extract_response_tool_calls(message['tool_calls'])
            
            # Create assistant message
            assistant_prompt_message = AssistantPromptMessage(
                content=content,
                tool_calls=tool_calls
            )
            
            # Calculate tokens
            if 'usage' in response_data:
                prompt_tokens = response_data['usage'].get('prompt_tokens', 0)
                completion_tokens = response_data['usage'].get('completion_tokens', 0)
            else:
                prompt_tokens = self._num_tokens_from_messages(model, prompt_messages, tools)
                completion_tokens = self._num_tokens_from_messages(model, [assistant_prompt_message])
            
            # Calculate usage
            usage = self._calc_response_usage(
                model, credentials, prompt_tokens, completion_tokens
            )
            usage.latency = time.time() - start_time
            
            # Create result
            result = LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=assistant_prompt_message,
                usage=usage,
                system_fingerprint=response_data.get('system_fingerprint'),
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to handle chat response: {e}")
            raise InvokeError(str(e))

    def _handle_chat_generate_response_from_data(
        self,
        model: str,
        credentials: dict,
        response_data: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
        start_time: float = 0,
    ) -> LLMResult:
        """
        Handle llm chat response from parsed JSON data
        """
        try:
            if 'choices' not in response_data or not response_data['choices']:
                raise InvokeError("Invalid response: no choices found")
                
            choice = response_data['choices'][0]
            message = choice.get('message', {})
            
            # Extract content and tool calls
            content = message.get('content', '')
            tool_calls = []
            
            if 'tool_calls' in message and message['tool_calls']:
                tool_calls = self._extract_response_tool_calls(message['tool_calls'])
                logger.info(f"Extracted {len(tool_calls)} tool calls from response")
                for i, tool_call in enumerate(tool_calls):
                    logger.info(f"Tool call {i+1}: {tool_call.function.name}")
            
            # Create assistant message
            assistant_prompt_message = AssistantPromptMessage(
                content=content,
                tool_calls=tool_calls
            )
            
            # Calculate tokens
            if 'usage' in response_data:
                prompt_tokens = response_data['usage'].get('prompt_tokens', 0)
                completion_tokens = response_data['usage'].get('completion_tokens', 0)
            else:
                prompt_tokens = self._num_tokens_from_messages(model, prompt_messages, tools)
                completion_tokens = self._num_tokens_from_messages(model, [assistant_prompt_message])
            
            # Calculate usage
            usage = self._calc_response_usage(
                model, credentials, prompt_tokens, completion_tokens
            )
            usage.latency = time.time() - start_time
            
            # Create result
            result = LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=assistant_prompt_message,
                usage=usage,
                system_fingerprint=response_data.get('system_fingerprint'),
            )
            
            logger.info(f"Successfully created LLMResult with content length: {len(content)}, tool_calls: {len(tool_calls)}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to handle chat response from data: {e}")
            raise InvokeError(str(e))

    def _handle_chat_generate_stream_response(
        self,
        model: str,
        credentials: dict,
        response,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
        start_time: float = 0,
    ) -> Generator:
        """
        Handle llm chat stream response

        :param model: model name
        :param response: response stream
        :param prompt_messages: prompt messages
        :param tools: tools for tool calling
        :param start_time: request start time
        :return: llm response chunk generator
        """
        full_content = ""
        prompt_tokens = 0
        completion_tokens = 0
        tool_calls = []
        tool_calls_dict = {}  # Use dict to avoid duplicates by tool call ID
        
        try:
            logger.info("Starting to process stream response")
            chunk_count = 0
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                line = line.decode('utf-8')
                logger.debug(f"Received line: {line[:100]}...")  # Log first 100 chars
                
                if not line.startswith('data: '):
                    continue
                    
                line = line[6:]  # Remove 'data: ' prefix
                if line.strip() == '[DONE]':
                    logger.info("Received [DONE] marker, ending stream")
                    break
                    
                try:
                    chunk_data = json.loads(line)
                    chunk_count += 1
                    logger.debug(f"Parsed chunk {chunk_count}: {chunk_data.keys() if isinstance(chunk_data, dict) else type(chunk_data)}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON chunk: {e}, line: {line[:100]}")
                    continue
                
                if 'choices' not in chunk_data or not chunk_data['choices']:
                    # Handle usage information
                    if 'usage' in chunk_data:
                        prompt_tokens = chunk_data['usage'].get('prompt_tokens', 0)
                        completion_tokens = chunk_data['usage'].get('completion_tokens', 0)
                    continue
                
                choice = chunk_data['choices'][0]
                delta = choice.get('delta', {})
                
                content = delta.get('content', '')
                if content:
                    full_content += content
                
                # Handle tool calls
                chunk_tool_calls = []
                if 'tool_calls' in delta and delta['tool_calls']:
                    logger.debug(f"Found tool_calls in chunk {chunk_count}: {delta['tool_calls']}")
                    
                    # Process each tool call in the delta
                    for tool_call_data in delta['tool_calls']:
                        tool_call_id = tool_call_data.get('id', '')
                        tool_call_index = tool_call_data.get('index', 0)
                        function_data = tool_call_data.get('function', {})
                        
                        if tool_call_id:
                            # This is a new tool call or the start of one
                            if tool_call_id not in tool_calls_dict:
                                # Create new tool call
                                function = AssistantPromptMessage.ToolCall.ToolCallFunction(
                                    name=function_data.get('name', ''),
                                    arguments=function_data.get('arguments', '') or '',
                                )
                                tool_call = AssistantPromptMessage.ToolCall(
                                    id=tool_call_id,
                                    type=tool_call_data.get('type', 'function'),
                                    function=function,
                                )
                                tool_calls_dict[tool_call_id] = tool_call
                                logger.info(f"New tool call started in chunk {chunk_count}: {function.name} (id: {tool_call_id})")
                            else:
                                # Update existing tool call with additional arguments
                                existing_tool_call = tool_calls_dict[tool_call_id]
                                additional_args = function_data.get('arguments', '') or ''
                                if additional_args:
                                    existing_tool_call.function.arguments += additional_args
                                    logger.debug(f"Updated tool call {tool_call_id} with additional arguments: '{additional_args}'")
                        else:
                            # Tool call without ID - this is likely a continuation of the previous tool call
                            # Find the most recent tool call and append to it
                            if tool_calls_dict:
                                # Get the last tool call (most recently added)
                                last_tool_call_id = list(tool_calls_dict.keys())[-1]
                                last_tool_call = tool_calls_dict[last_tool_call_id]
                                additional_args = function_data.get('arguments', '') or ''
                                if additional_args:
                                    last_tool_call.function.arguments += additional_args
                                    logger.debug(f"Appended to last tool call {last_tool_call_id}: '{additional_args}'")
                    
                    # Update the tool_calls list from dict
                    tool_calls = list(tool_calls_dict.values())
                    
                    # Log current state
                    logger.debug(f"Total unique tool calls so far: {len(tool_calls)}")
                    for i, tool_call in enumerate(tool_calls):
                        logger.debug(f"Tool call {i+1}: {tool_call.function.name} (id: {tool_call.id}) - args: '{tool_call.function.arguments}'")
                
                # Get finish reason first
                finish_reason = choice.get('finish_reason')
                if finish_reason:
                    logger.info(f"Chunk {chunk_count} finish_reason: {finish_reason}")
                
                # Create assistant message
                # Only include tool calls in the message when we have the finish_reason
                message_tool_calls = []
                if finish_reason == 'tool_calls' and tool_calls_dict:
                    # Include all accumulated tool calls in the final message
                    message_tool_calls = list(tool_calls_dict.values())
                    logger.info(f"Including all {len(message_tool_calls)} tool calls in assistant message")
                    # Log the complete tool calls
                    for i, tool_call in enumerate(message_tool_calls):
                        logger.info(f"Final tool call {i+1}: {tool_call.function.name} - args: {tool_call.function.arguments}")
                
                assistant_prompt_message = AssistantPromptMessage(
                    content=content,
                    tool_calls=message_tool_calls
                )
                
                # Create chunk
                chunk = LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    system_fingerprint=chunk_data.get('system_fingerprint'),
                    delta=LLMResultChunkDelta(
                        index=choice.get('index', 0),
                        message=assistant_prompt_message,
                        finish_reason=finish_reason,
                    ),
                )
                
                yield chunk
                
                # The main chunk already contains the tool calls, no need for additional chunks
                # Just log when we encounter tool_calls finish reason
                if finish_reason == 'tool_calls':
                    logger.info(f"Tool calls completed in chunk {chunk_count} with {len(message_tool_calls)} tool calls")
            
            logger.info(f"Stream processing completed. Chunks processed: {chunk_count}")
            logger.info(f"Full content length: {len(full_content)}")
            logger.info(f"Tool calls found: {len(tool_calls)}")
            
            # If no chunks were processed, this might indicate an issue
            if chunk_count == 0:
                logger.warning("No chunks were processed from the stream response")
                logger.warning("This might indicate the response format is not as expected")
                # Try to read the response as text to see what we actually got
                try:
                    response.encoding = 'utf-8'
                    response_text = response.text
                    logger.error(f"Raw response text: {response_text[:1000]}")
                    if response_text.strip():
                        # Try to parse as JSON
                        try:
                            response_data = json.loads(response_text)
                            logger.info("Response appears to be JSON, processing as non-stream")
                            return self._handle_chat_generate_response_from_data(
                                model, credentials, response_data, prompt_messages, tools, start_time
                            )
                        except json.JSONDecodeError:
                            logger.error("Response is not valid JSON either")
                except Exception as e:
                    logger.error(f"Failed to read response text: {e}")
                
                raise InvokeError("No valid response chunks received from stream")
            
            # Calculate final usage if not provided
            if not prompt_tokens:
                prompt_tokens = self._num_tokens_from_messages(model, prompt_messages, tools)
            if not completion_tokens:
                # Use the accumulated tool calls from the dict
                final_tool_calls = list(tool_calls_dict.values())
                full_assistant_message = AssistantPromptMessage(content=full_content, tool_calls=final_tool_calls)
                completion_tokens = self._num_tokens_from_messages(model, [full_assistant_message])
                
            # Update tool_calls with final accumulated calls
            tool_calls = list(tool_calls_dict.values())
            logger.info(f"Final tool calls count: {len(tool_calls)}")
            if tool_calls:
                for i, tool_call in enumerate(tool_calls):
                    logger.info(f"Final tool call {i+1}: {tool_call.function.name} (id: {tool_call.id})")
                    logger.info(f"Final tool call {i+1} arguments: {tool_call.function.arguments}")
            
            # Calculate usage
            usage = self._calc_response_usage(
                model, credentials, prompt_tokens, completion_tokens
            )
            usage.latency = time.time() - start_time
            
            logger.info(f"Final usage - prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}")
            
            # Yield final chunk with usage
            final_chunk = LLMResultChunk(
                model=model,
                prompt_messages=prompt_messages,
                delta=LLMResultChunkDelta(
                    index=0,
                    message=AssistantPromptMessage(content=""),
                    finish_reason="stop",
                    usage=usage,
                ),
            )
            
            yield final_chunk
            
        except Exception as e:
            logger.error(f"Failed to handle stream response: {e}")
            raise InvokeError(str(e))

    def _extract_response_tool_calls(
        self,
        response_tool_calls: List[Dict[str, Any]],
    ) -> list[AssistantPromptMessage.ToolCall]:
        """
        Extract tool calls from response

        :param response_tool_calls: response tool calls
        :return: list of tool calls
        """
        tool_calls = []
        if response_tool_calls:
            logger.debug(f"Processing {len(response_tool_calls)} tool calls from response")
            for i, response_tool_call in enumerate(response_tool_calls):
                logger.debug(f"Processing tool call {i+1}: {response_tool_call}")
                if 'function' in response_tool_call:
                    function_data = response_tool_call['function']
                    function = AssistantPromptMessage.ToolCall.ToolCallFunction(
                        name=function_data.get('name', ''),
                        arguments=function_data.get('arguments', ''),
                    )

                    tool_call = AssistantPromptMessage.ToolCall(
                        id=response_tool_call.get('id', ''),
                        type=response_tool_call.get('type', 'function'),
                        function=function,
                    )
                    tool_calls.append(tool_call)
                    logger.debug(f"Created tool call: id={tool_call.id}, name={function.name}")
                else:
                    logger.warning(f"Tool call {i+1} missing 'function' field: {response_tool_call}")

        logger.debug(f"Extracted {len(tool_calls)} valid tool calls")
        return tool_calls

    def _convert_prompt_message_to_dict(self, message: PromptMessage) -> dict:
        """
        Convert PromptMessage to dict for Gateway API
        """
        def clean_content(content):
            """Clean content to handle potential encoding issues"""
            if not isinstance(content, str):
                return content
            
            try:
                # 检查字符串是否可以正确编码
                content.encode('utf-8')
                
                # 移除可能导致问题的控制字符，但保留常见的空白字符
                import re
                # 保留换行符、制表符和回车符，但移除其他控制字符
                cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
                
                # 规范化连续的空白字符
                cleaned = re.sub(r'\s+', ' ', cleaned.strip())
                
                return cleaned
                
            except UnicodeEncodeError as e:
                logger.warning(f"Content encoding issue: {e}")
                # 使用替换字符处理编码问题
                return content.encode('utf-8', errors='replace').decode('utf-8')
            except Exception as e:
                logger.error(f"Unexpected error cleaning content: {e}")
                return str(content)  # 转换为字符串作为备用方案
        
        if isinstance(message, UserPromptMessage):
            message = cast(UserPromptMessage, message)
            if isinstance(message.content, str):
                cleaned_content = clean_content(message.content)
                message_dict = {"role": "user", "content": cleaned_content}
            else:
                # Handle complex content types
                content_parts = []
                assert isinstance(message.content, list)
                for content in message.content:
                    if content.type == PromptMessageContentType.TEXT:
                        content = cast(TextPromptMessageContent, content)
                        cleaned_text = clean_content(content.data)
                        content_parts.append({"type": "text", "text": cleaned_text})
                    # Add support for other content types if needed
                
                if len(content_parts) == 1 and content_parts[0]["type"] == "text":
                    message_dict = {"role": "user", "content": content_parts[0]["text"]}
                else:
                    message_dict = {"role": "user", "content": content_parts}
                    
        elif isinstance(message, AssistantPromptMessage):
            message = cast(AssistantPromptMessage, message)
            cleaned_content = clean_content(message.content) if message.content else ""
            message_dict = {"role": "assistant", "content": cleaned_content}

            # Add tool calls if present
            if message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type or "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": clean_content(tool_call.function.arguments) if tool_call.function.arguments else "",
                        },
                    }
                    for tool_call in message.tool_calls
                ]
        elif isinstance(message, SystemPromptMessage):
            message = cast(SystemPromptMessage, message)
            cleaned_content = clean_content(message.content) if message.content else ""
            message_dict = {"role": "system", "content": cleaned_content}
        elif isinstance(message, ToolPromptMessage):
            message = cast(ToolPromptMessage, message)
            cleaned_content = clean_content(message.content) if message.content else ""
            message_dict = {
                "role": "tool",
                "content": cleaned_content,
                "tool_call_id": message.tool_call_id,
            }
        else:
            raise ValueError(f"Got unknown type {message}")

        if message.name and message_dict.get("role") != "tool":
            message_dict["name"] = message.name

        return message_dict

    def _num_tokens_from_messages(
        self,
        model: str,
        messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        """
        Calculate num tokens for messages with tiktoken package.

        :param model: model name
        :param messages: prompt messages
        :param tools: tools for tool calling
        :return: number of tokens
        """
        try:
            # Use a default encoding for token calculation
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to a simple character-based estimation
            total_chars = sum(len(str(msg.content)) for msg in messages if msg.content)
            return total_chars // 4  # Rough estimation: 4 characters per token

        num_tokens = 0
        messages_dict = [self._convert_prompt_message_to_dict(m) for m in messages]
        
        # Base tokens per message
        tokens_per_message = 3
        tokens_per_name = 1
        
        for message in messages_dict:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))
                elif isinstance(value, list):
                    # Handle complex content
                    for item in value:
                        if isinstance(item, dict) and "text" in item:
                            num_tokens += len(encoding.encode(item["text"]))
                elif key == "tool_calls" and isinstance(value, list):
                    # Handle tool calls
                    for tool_call in value:
                        if isinstance(tool_call, dict):
                            num_tokens += len(encoding.encode(json.dumps(tool_call)))
                
                if key == "name":
                    num_tokens += tokens_per_name

        # Add tokens for the assistant's reply
        num_tokens += 3

        # Add tokens for tools
        if tools:
            for tool in tools:
                num_tokens += len(encoding.encode(tool.name))
                num_tokens += len(encoding.encode(tool.description))
                num_tokens += len(encoding.encode(json.dumps(tool.parameters)))

        return num_tokens

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        Map model invoke error to unified error
        The key is the error type thrown to the caller
        The value is the error type thrown by the model,
        which needs to be converted into a unified error type for the caller.

        :return: Invoke error mapping
        """
        return {
            InvokeConnectionError: [ConnectionError, requests.exceptions.ConnectionError],
            InvokeServerUnavailableError: [requests.exceptions.HTTPError],
            InvokeRateLimitError: [],
            InvokeAuthorizationError: [requests.exceptions.HTTPError],
            InvokeBadRequestError: [ValueError, requests.exceptions.HTTPError, KeyError],
        }

    def get_customizable_model_schema(self, model: str, credentials: dict) -> Optional[AIModelEntity]:
        """
        Get customizable model schema for custom models.
        
        :param model: model name
        :param credentials: model credentials
        :return: AIModelEntity or None if model not found
        """
        try:
            # Get predefined models using LargeLanguageModel's method
            models = LargeLanguageModel.predefined_models(self)
            model_map = {m.model: m for m in models}
            
            logger.info(f"Available predefined models: {list(model_map.keys())}")
            logger.info(f"Looking for model: {model}")
            
            # If model exists in predefined models, use it as base
            if model in model_map:
                base_model_schema = model_map[model]
                logger.info(f"Found exact match for model {model}")
            else:
                # For custom models, use deepseek-v3 as default template
                base_model_schema = model_map.get("deepseek-v3")
                if not base_model_schema:
                    logger.warning(f"No base model found for {model} and no deepseek-v3 template available")
                    return None
                logger.info(f"Using deepseek-v3 as template for model {model}")
            
            # Create customizable model entity
            entity = AIModelEntity(
                model=model,
                label=I18nObject(zh_Hans=model, en_US=model),
                model_type=ModelType.LLM,
                features=base_model_schema.features or [],
                fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
                model_properties=dict(base_model_schema.model_properties.items()) if base_model_schema.model_properties else {},
                parameter_rules=list(base_model_schema.parameter_rules) if base_model_schema.parameter_rules else [],
                pricing=base_model_schema.pricing,
            )
            
            logger.info(f"Successfully created customizable model schema for {model}")
            return entity
            
        except Exception as e:
            logger.error(f"Failed to get customizable model schema for {model}: {e}")
            return None
