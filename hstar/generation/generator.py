"""LLM generator for calling Azure OpenAI API."""

import time
from typing import Optional, Dict, Any, List
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from hstar.config import Config


class Generator:
    """
    Generator class for calling Azure OpenAI API with retry logic.
    """
    
    def __init__(self, config: Config):
        """
        Initialize generator with configuration.
        
        Args:
            config: Configuration object with Azure OpenAI settings
        """
        self.config = config
        self.client = self._setup_client()
    
    def _setup_client(self) -> AzureOpenAI:
        """Setup Azure OpenAI client with DefaultAzureCredential."""
        credential = DefaultAzureCredential()
        
        client = AzureOpenAI(
            azure_endpoint=self.config.azure_endpoint,
            api_version=self.config.azure_api_version,
            azure_deployment=self.config.azure_deployment,
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token
        )
        
        return client
    
    def generate(
        self,
        prompt: str,
        system_message: str = "You are a helpful AI assistant.",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """
        Generate completion from prompt with retry logic.
        
        Args:
            prompt: User prompt to send to the model
            system_message: System message to set context
            temperature: Sampling temperature (default: from config)
            max_tokens: Maximum tokens to generate (default: from config)
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If all retry attempts fail
        """
        temp = temperature if temperature is not None else self.config.temperature_text
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.azure_deployment,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temp,
                    # max_tokens=tokens
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {e}")
    
    def generate_with_metadata(
        self,
        prompt: str,
        system_message: str = "You are a helpful AI assistant.",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate completion and return with metadata.
        
        Args:
            prompt: User prompt to send to the model
            system_message: System message to set context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with 'text', 'finish_reason', and usage statistics
        """
        temp = temperature if temperature is not None else self.config.temperature_text
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        response = self.client.chat.completions.create(
            model=self.config.azure_deployment,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temp,
            # max_tokens=tokens
        )
        
        return {
            "text": response.choices[0].message.content.strip(),
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
