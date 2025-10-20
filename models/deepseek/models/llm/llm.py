import logging
import time
from collections.abc import Generator
from typing import Optional, Union
from dify_plugin.entities.model.llm import LLMMode, LLMResult
from dify_plugin.entities.model.message import PromptMessage, PromptMessageTool
from yarl import URL
from dify_plugin import OAICompatLargeLanguageModel

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
    logger.setLevel(logging.INFO)

# 测试日志配置
logger.info("DeepSeek: Module loaded, logger configured successfully")


class DeepseekLargeLanguageModel(OAICompatLargeLanguageModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("DeepSeek: LargeLanguageModel initialized with debug logging enabled")
    
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
        # 添加详细的调试日志
        logger.info(f"DeepSeek: Starting chat generation for model: {model}")
        logger.info(f"DeepSeek: Stream mode: {stream}")
        logger.info(f"DeepSeek: Number of prompt messages: {len(prompt_messages)}")
        logger.info(f"DeepSeek: Tools provided: {len(tools) if tools else 0}")
        logger.info(f"DeepSeek: Model parameters: {model_parameters}")
        
        # Log tool information if tools are provided
        if tools:
            logger.info("DeepSeek: Tool calling enabled - tools:")
            for i, tool in enumerate(tools):
                logger.info(f"DeepSeek:   Tool {i+1}: {tool.name} - {tool.description}")
                logger.debug(f"DeepSeek:   Tool {i+1} parameters: {tool.parameters}")
        
        # Log message details
        for i, msg in enumerate(prompt_messages):
            content_length = len(str(msg.content)) if msg.content else 0
            logger.info(f"DeepSeek: Message {i}: role={type(msg).__name__}, content_length={content_length}")
            if content_length < 100:
                logger.debug(f"DeepSeek: Message {i} content: {msg.content}")
        
        self._add_custom_parameters(credentials)
        
        # Log credentials after adding custom parameters
        logger.info(f"DeepSeek: Endpoint URL: {credentials.get('endpoint_url')}")
        logger.info(f"DeepSeek: Function calling type: {credentials.get('function_calling_type')}")
        logger.info(f"DeepSeek: Stream function calling: {credentials.get('stream_function_calling')}")
        
        start_time = time.time()
        result = super()._invoke(model, credentials, prompt_messages, model_parameters, tools, stop, stream, user)
        
        if not stream:
            # For non-stream responses, log the result
            if isinstance(result, LLMResult):
                logger.info(f"DeepSeek: Response received - content_length: {len(result.message.content) if result.message.content else 0}")
                logger.info(f"DeepSeek: Tool calls in response: {len(result.message.tool_calls) if result.message.tool_calls else 0}")
                if result.message.tool_calls:
                    for i, tool_call in enumerate(result.message.tool_calls):
                        logger.info(f"DeepSeek: Tool call {i+1}: {tool_call.function.name}")
                logger.info(f"DeepSeek: Response latency: {time.time() - start_time:.2f}s")
        else:
            logger.info(f"DeepSeek: Returning stream generator")
            # Wrap the generator to add logging
            result = self._wrap_stream_generator(result, model, start_time)
        
        return result
    
    def _wrap_stream_generator(self, generator, model: str, start_time: float):
        """
        Wrap the stream generator to add detailed logging
        """
        logger.info(f"DeepSeek: Starting to process stream response for model: {model}")
        chunk_count = 0
        full_content = ""
        tool_calls_found = []
        
        try:
            for chunk in generator:
                chunk_count += 1
                logger.debug(f"DeepSeek: Processing chunk {chunk_count}")
                
                if hasattr(chunk, 'delta') and chunk.delta:
                    if hasattr(chunk.delta, 'message') and chunk.delta.message:
                        message = chunk.delta.message
                        
                        # Log content
                        if hasattr(message, 'content') and message.content:
                            content_length = len(message.content)
                            full_content += message.content
                            logger.debug(f"DeepSeek: Chunk {chunk_count} content length: {content_length}")
                        
                        # Log tool calls
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                if hasattr(tool_call, 'function') and tool_call.function:
                                    tool_calls_found.append(tool_call.function.name)
                                    logger.info(f"DeepSeek: Tool call found in chunk {chunk_count}: {tool_call.function.name}")
                    
                    # Log finish reason
                    if hasattr(chunk.delta, 'finish_reason') and chunk.delta.finish_reason:
                        logger.info(f"DeepSeek: Chunk {chunk_count} finish_reason: {chunk.delta.finish_reason}")
                
                yield chunk
            
            # Log final statistics
            logger.info(f"DeepSeek: Stream processing completed")
            logger.info(f"DeepSeek: Total chunks processed: {chunk_count}")
            logger.info(f"DeepSeek: Full content length: {len(full_content)}")
            logger.info(f"DeepSeek: Tool calls found: {len(set(tool_calls_found))}")
            if tool_calls_found:
                logger.info(f"DeepSeek: Tool call names: {list(set(tool_calls_found))}")
            logger.info(f"DeepSeek: Total latency: {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"DeepSeek: Error in stream processing: {e}")
            raise

    def validate_credentials(self, model: str, credentials: dict) -> None:
        self._add_custom_parameters(credentials)
        super().validate_credentials(model, credentials)

    @staticmethod
    def _add_custom_parameters(credentials) -> None:
        credentials["endpoint_url"] = str(URL(credentials.get("endpoint_url", "https://api.deepseek.com")))
        credentials["mode"] = LLMMode.CHAT.value
        credentials["function_calling_type"] = "tool_call"
        credentials["stream_function_calling"] = "support"
