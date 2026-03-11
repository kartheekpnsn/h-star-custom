"""Configuration module for H-STAR pipeline."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for H-STAR pipeline."""
    
    # Azure OpenAI settings
    azure_endpoint: str = ""
    azure_deployment: str = ""
    azure_api_version: str = "2024-02-15-preview"
    
    # Pipeline settings
    temperature_sql: float = 0.1
    temperature_text: float = 0.3
    max_tokens: int = 512
    n_shots: int = 2
    
    # Table formatting
    prompt_style: str = "create_table"  # Options: create_table, transpose, text
    max_table_rows: int = 50
    
    # Result settings
    results_dir: str = "results"
    save_intermediate: bool = False
    
    # Database settings
    db_path: str = ":memory:"
    table_name: str = "dataset"
    
    def __post_init__(self):
        """Load environment variables if not already set."""
        if not self.azure_endpoint or not self.azure_deployment:
            load_dotenv()
            self.azure_endpoint = self.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")
            self.azure_deployment = self.azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
            
        if not self.azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT must be set in .env or passed to Config")
        if not self.azure_deployment:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT must be set in .env or passed to Config")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        load_dotenv()
        return cls(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        )
