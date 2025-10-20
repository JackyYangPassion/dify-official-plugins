import logging
from collections.abc import Mapping
from typing import Optional

from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType, AIModelEntity
from dify_plugin.errors.model import CredentialsValidateFailedError

logger = logging.getLogger(__name__)


class CompanyGatewayProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        """
        Validate provider credentials
        if validate failed, raise exception

        :param credentials: provider credentials, credentials form defined in `provider_credential_schema`.
        """
        try:
            model_instance = self.get_model_instance(ModelType.LLM)

            # Use a simple model for validation
            model_instance.validate_credentials(
                model="deepseek-v3", credentials=credentials
            )
        except CredentialsValidateFailedError as ex:
            raise ex
        except Exception as ex:
            logger.exception(
                f"{self.get_provider_schema().provider} credentials validate failed"
            )
            raise ex

    def get_model_schema(self, model: str, credentials: Mapping) -> Optional[AIModelEntity]:
        """
        Get model schema for the specified model.
        
        :param model: model name
        :param credentials: model credentials
        :return: model schema or None
        """
        try:
            model_instance = self.get_model_instance(ModelType.LLM)
            
            logger.info(f"Getting model schema for {model}")
            
            # First check if model exists in predefined models
            from dify_plugin import LargeLanguageModel
            predefined_models = LargeLanguageModel.predefined_models(model_instance)
            logger.info(f"Found {len(predefined_models)} predefined models")
            
            for predefined_model in predefined_models:
                if predefined_model.model == model:
                    logger.info(f"Found predefined model schema for {model}")
                    return predefined_model
            
            # Try to get customizable model schema if not found in predefined
            if hasattr(model_instance, 'get_customizable_model_schema'):
                logger.info(f"Trying customizable model schema for {model}")
                # Ensure credentials is not None
                safe_credentials = credentials or {}
                schema = model_instance.get_customizable_model_schema(model, safe_credentials)
                if schema:
                    logger.info(f"Created customizable model schema for {model}")
                    return schema
                    
            logger.warning(f"No model schema found for {model}")
            return None
            
        except Exception as ex:
            logger.exception(f"Failed to get model schema for {model}: {ex}")
            return None
