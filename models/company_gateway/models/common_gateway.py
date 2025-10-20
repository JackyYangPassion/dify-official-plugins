import json
import logging
from typing import Optional, Union, Any, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dify_plugin.entities.model import PriceType
from dify_plugin.entities.model.llm import LLMUsage

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


class _CommonGateway:
    """
    Common Gateway API client for company internal gateway
    """
    
    def __init__(self):
        # Setup session with retry strategy
        self.session = requests.Session()
        
        # Handle urllib3 version compatibility
        retry_kwargs = {
            "total": 3,
            "status_forcelist": [429, 500, 502, 503, 504],
            "backoff_factor": 1
        }
        
        # Try newer parameter name first, fallback to older one
        try:
            retry_strategy = Retry(
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
                **retry_kwargs
            )
        except TypeError:
            # Fallback for older urllib3 versions
            retry_strategy = Retry(
                method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
                **retry_kwargs
            )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _to_credential_kwargs(self, credentials: dict) -> dict:
        """
        Transform credentials to kwargs for HTTP requests
        """
        kwargs = {}
        
        # Base URL (remove trailing slash as model name will be appended)
        api_base_url = credentials.get('api_base_url', 'http://xyz.cn')
        if api_base_url.endswith('/'):
            api_base_url = api_base_url[:-1]
        kwargs['base_url'] = api_base_url
        
        # API Key
        api_key = credentials.get('api_key')
        if api_key:
            kwargs['api_key'] = api_key
        
        # Custom headers
        custom_header_name = credentials.get('custom_header_name')
        custom_header_value = credentials.get('custom_header_value')
        if custom_header_name and custom_header_value:
            kwargs['custom_headers'] = {custom_header_name: custom_header_value}
        
        return kwargs

    def _prepare_headers(self, api_key: str, custom_headers: Optional[Dict[str, str]] = None) -> dict:
        """
        Prepare HTTP headers for API requests
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        if custom_headers:
            headers.update(custom_headers)
            
        return headers

    def _build_curl_command(self, method: str, url: str, headers: dict, data: Optional[dict] = None) -> str:
        """
        构建等效的 curl 命令字符串用于调试
        按照 Dify 文档要求输出 curl 格式的日志
        """
        try:
            curl_cmd = f"curl -X {method} '{url}'"
            
            # 添加请求头
            if headers:
                for key, value in headers.items():
                    # 对包含敏感信息的头部进行脱敏处理
                    if key.lower() in ['authorization', 'api-key']:
                        if value.startswith('Bearer '):
                            # 保留前几位和后几位，中间用星号代替
                            masked_value = f"Bearer {value[7:11]}...{value[-4:]}" if len(value) > 15 else "Bearer ***"
                        else:
                            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                        curl_cmd += f" -H '{key}: {masked_value}'"
                    else:
                        curl_cmd += f" -H '{key}: {value}'"
            
            # 添加请求体数据
            if data:
                # 为了避免日志过长，对数据进行适当的处理
                data_copy = data.copy()
                
                # 处理消息内容，避免记录完整的敏感内容
                if 'messages' in data_copy:
                    messages_summary = []
                    for i, msg in enumerate(data_copy['messages']):
                        content = msg.get('content', '')
                        if isinstance(content, str):
                            # 根据内容长度决定显示策略
                            if len(content) <= 100:
                                # 短内容完整显示
                                content_display = content
                            else:
                                # 长内容显示前50个字符
                                content_display = content[:50] + '...'
                            
                            messages_summary.append({
                                'role': msg.get('role'),
                                'content': content_display,
                                'content_length': len(content)
                            })
                        else:
                            messages_summary.append({
                                'role': msg.get('role'),
                                'content_type': type(content).__name__
                            })
                    data_copy['messages'] = messages_summary
                
                # 序列化数据
                data_str = json.dumps(data_copy, ensure_ascii=False, indent=None, separators=(',', ':'))
                
                # 如果数据太长，进行截断
                if len(data_str) > 2000:
                    data_str = data_str[:2000] + '...[truncated]'
                
                # 转义单引号以避免命令行问题
                data_str = data_str.replace("'", "\\'")
                curl_cmd += f" -d '{data_str}'"
            
            return curl_cmd
            
        except Exception as e:
            logger.error(f"Failed to build curl command: {e}")
            return f"curl -X {method} '{url}' # Error building full command: {e}"

    def _clean_request_data(self, data: dict) -> dict:
        """
        Clean request data to handle potential encoding issues
        """
        try:
            import json
            import re
            
            def clean_string(text):
                if not isinstance(text, str):
                    return text
                
                # 移除可能导致问题的控制字符
                text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
                
                # 确保字符串可以正确编码为UTF-8
                try:
                    text.encode('utf-8')
                    return text
                except UnicodeEncodeError:
                    # 如果有编码问题，使用替换字符
                    return text.encode('utf-8', errors='replace').decode('utf-8')
            
            def clean_dict(obj):
                if isinstance(obj, dict):
                    return {k: clean_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [clean_dict(item) for item in obj]
                elif isinstance(obj, str):
                    return clean_string(obj)
                else:
                    return obj
            
            cleaned_data = clean_dict(data)
            
            # 验证清理后的数据可以序列化
            json.dumps(cleaned_data, ensure_ascii=False)
            logger.info("Successfully cleaned request data")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to clean request data: {e}")
            # 如果清理失败，返回原数据
            return data

    def _make_request(
        self,
        method: str,
        url: str,
        headers: dict,
        data: Optional[dict] = None,
        stream: bool = False,
        timeout: int = 60
    ) -> requests.Response:
        """
        Make HTTP request to gateway API
        """
        try:
            # 按照 Dify 文档要求输出 curl 格式的日志
            curl_command = self._build_curl_command(method, url, headers, data)
            logger.info(f"Generated cURL command: {curl_command}")
            
            # 添加调试日志
            logger.info(f"Making request to: {method} {url}")
            logger.debug(f"Headers count: {len(headers)}")
            
            if data:
                # 安全地记录请求数据，避免记录敏感信息
                safe_data = data.copy()
                if 'messages' in safe_data:
                    # 记录消息数量和内容长度，而不是完整内容
                    messages_info = []
                    for i, msg in enumerate(safe_data['messages']):
                        msg_info = {
                            'index': i,
                            'role': msg.get('role', 'unknown'),
                            'content_length': len(str(msg.get('content', ''))) if msg.get('content') else 0,
                            'content_type': type(msg.get('content', '')).__name__
                        }
                        # 如果内容较短，可以记录完整内容用于调试
                        if msg_info['content_length'] < 100:
                            msg_info['content_preview'] = str(msg.get('content', ''))[:50]
                        messages_info.append(msg_info)
                    
                    safe_data['messages'] = messages_info
                
                logger.debug(f"Request data structure: {safe_data}")
            
            # 确保请求数据正确编码
            json_data = None
            if data:
                try:
                    # 预先序列化检查是否有编码问题
                    import json
                    json_str = json.dumps(data, ensure_ascii=False)
                    logger.debug(f"JSON payload size: {len(json_str.encode('utf-8'))} bytes")
                    json_data = data
                except (TypeError, UnicodeEncodeError) as e:
                    logger.error(f"JSON serialization error: {e}")
                    # 尝试清理数据
                    json_data = self._clean_request_data(data)
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                stream=stream,
                timeout=timeout
            )
            
            logger.info(f"Response status: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"Response headers: {response.headers}")
                logger.error(f"Response body preview: {response.text[:500]}")
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request method: {method}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Error response status: {e.response.status_code}")
                logger.error(f"Error response text: {e.response.text[:500]}")
            raise

    def _extract_error_message(self, response: requests.Response) -> str:
        """
        Extract error message from response
        """
        try:
            error_data = response.json()
            if 'error' in error_data:
                if isinstance(error_data['error'], dict):
                    return error_data['error'].get('message', str(error_data['error']))
                return str(error_data['error'])
            return error_data.get('message', f'HTTP {response.status_code}')
        except (json.JSONDecodeError, ValueError):
            return f'HTTP {response.status_code}: {response.text[:200]}'

    def _calc_response_usage(
        self,
        model: str,
        credentials: dict,
        prompt_tokens: int,
        completion_tokens: int
    ) -> LLMUsage:
        """
        Calculate response usage and cost
        """
        # Get pricing information for prompt and completion tokens
        prompt_price_info = self.get_price(
            model=model, 
            credentials=credentials, 
            price_type=PriceType.INPUT, 
            tokens=prompt_tokens
        )
        completion_price_info = self.get_price(
            model=model, 
            credentials=credentials, 
            price_type=PriceType.OUTPUT, 
            tokens=completion_tokens
        )
        
        # Create usage object
        usage = LLMUsage(
            prompt_tokens=prompt_tokens,
            prompt_unit_price=prompt_price_info.unit_price,
            prompt_price_unit=prompt_price_info.unit,
            prompt_price=prompt_price_info.total_amount,
            completion_tokens=completion_tokens,
            completion_unit_price=completion_price_info.unit_price,
            completion_price_unit=completion_price_info.unit,
            completion_price=completion_price_info.total_amount,
            total_tokens=prompt_tokens + completion_tokens,
            total_price=prompt_price_info.total_amount + completion_price_info.total_amount,
            currency=prompt_price_info.currency,
            latency=0.0  # This should be set by the caller
        )
        
        return usage



    def get_model_mode(self, model: str, credentials: Optional[dict] = None):
        """
        Get model mode (chat for all our models)
        """
        from dify_plugin.entities.model.llm import LLMMode
        return LLMMode.CHAT

    def predefined_models(self):
        """
        Get predefined models - this method should not be called from _CommonGateway
        The LargeLanguageModel class will handle predefined models from YAML files
        """
        # This should not be called in practice since LargeLanguageModel.predefined_models() 
        # will be used instead via method resolution order
        return []

    def enforce_stop_tokens(self, text: str, stop_tokens: list[str]) -> str:
        """
        Enforce stop tokens in the generated text
        """
        if not stop_tokens:
            return text
            
        for stop_token in stop_tokens:
            if stop_token in text:
                text = text[:text.index(stop_token)]
                
        return text
