import json
import logging
from typing import Optional, Union, Any, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from dify_plugin.entities.model import PriceType
from dify_plugin.entities.model.llm import LLMUsage

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
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                stream=stream,
                timeout=timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
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
