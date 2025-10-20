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
        
        # Convert prompt messages to OpenAI format
        messages = [self._convert_prompt_message_to_dict(m) for m in prompt_messages]
        
        # Prepare request data (model is in URL, not in body)
        request_data = {
            "messages": messages,
            "stream": stream,
            **model_parameters
        }
        
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
        
        # Add stop tokens
        if stop:
            request_data["stop"] = stop
            
        # Add user if provided
        if user:
            request_data["user"] = user

        start_time = time.time()
        
        try:
            # Make request
            response = self._make_request(
                method="POST",
                url=url,
                headers=headers,
                data=request_data,
                stream=stream,
                timeout=120
            )
            
            if stream:
                return self._handle_chat_generate_stream_response(
                    model, credentials, response, prompt_messages, tools, start_time
                )
            else:
                return self._handle_chat_generate_response(
                    model, credentials, response, prompt_messages, tools, start_time
                )
                
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
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
        
        try:
            for line in response.iter_lines():
                if not line:
                    continue
                    
                line = line.decode('utf-8')
                if not line.startswith('data: '):
                    continue
                    
                line = line[6:]  # Remove 'data: ' prefix
                if line.strip() == '[DONE]':
                    break
                    
                try:
                    chunk_data = json.loads(line)
                except json.JSONDecodeError:
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
                if 'tool_calls' in delta and delta['tool_calls']:
                    chunk_tool_calls = self._extract_response_tool_calls(delta['tool_calls'])
                    tool_calls.extend(chunk_tool_calls)
                
                # Create assistant message
                assistant_prompt_message = AssistantPromptMessage(
                    content=content,
                    tool_calls=chunk_tool_calls if 'tool_calls' in delta else []
                )
                
                # Create chunk
                chunk = LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    system_fingerprint=chunk_data.get('system_fingerprint'),
                    delta=LLMResultChunkDelta(
                        index=choice.get('index', 0),
                        message=assistant_prompt_message,
                        finish_reason=choice.get('finish_reason'),
                    ),
                )
                
                yield chunk
            
            # Calculate final usage if not provided
            if not prompt_tokens:
                prompt_tokens = self._num_tokens_from_messages(model, prompt_messages, tools)
            if not completion_tokens:
                full_assistant_message = AssistantPromptMessage(content=full_content, tool_calls=tool_calls)
                completion_tokens = self._num_tokens_from_messages(model, [full_assistant_message])
            
            # Calculate usage
            usage = self._calc_response_usage(
                model, credentials, prompt_tokens, completion_tokens
            )
            usage.latency = time.time() - start_time
            
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
            for response_tool_call in response_tool_calls:
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

        return tool_calls

    def _convert_prompt_message_to_dict(self, message: PromptMessage) -> dict:
        """
        Convert PromptMessage to dict for Gateway API
        """
        if isinstance(message, UserPromptMessage):
            message = cast(UserPromptMessage, message)
            if isinstance(message.content, str):
                message_dict = {"role": "user", "content": message.content}
            else:
                # Handle complex content types
                content_parts = []
                assert isinstance(message.content, list)
                for content in message.content:
                    if content.type == PromptMessageContentType.TEXT:
                        content = cast(TextPromptMessageContent, content)
                        content_parts.append({"type": "text", "text": content.data})
                    # Add support for other content types if needed
                
                if len(content_parts) == 1 and content_parts[0]["type"] == "text":
                    message_dict = {"role": "user", "content": content_parts[0]["text"]}
                else:
                    message_dict = {"role": "user", "content": content_parts}
                    
        elif isinstance(message, AssistantPromptMessage):
            message = cast(AssistantPromptMessage, message)
            message_dict = {"role": "assistant", "content": message.content}

            # Add tool calls if present
            if message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type or "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ]
        elif isinstance(message, SystemPromptMessage):
            message = cast(SystemPromptMessage, message)
            message_dict = {"role": "system", "content": message.content}
        elif isinstance(message, ToolPromptMessage):
            message = cast(ToolPromptMessage, message)
            message_dict = {
                "role": "tool",
                "content": message.content,
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
