"""Configuration module for H-STAR pipeline."""

import os
from dataclasses import dataclass, field
from typing import List, Optional
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
    save_intermediate: bool = True
    
    # Databricks settings
    server_hostname: str = ""
    http_path: str = ""
    table_name: str = "dataset"
    table_names: List[str] = field(default_factory=list)
    schema: str = ""  # catalog.schema for auto-discovery (e.g. hive_metastore.piiq)
    
    def __post_init__(self):
        """Load environment variables if not already set."""
        load_dotenv()
        self.azure_endpoint = self.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_deployment = self.azure_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        self.server_hostname = self.server_hostname or os.getenv("DATABRICKS_SERVER_HOSTNAME", "")
        self.http_path = self.http_path or os.getenv("DATABRICKS_HTTP_PATH", "")
        self.table_name = os.getenv("HSTAR_TABLE_NAME", self.table_name)

        # Schema auto-discovery setting
        self.schema = self.schema or os.getenv("HSTAR_SCHEMA", "")

        # Multi-table support: parse comma-separated HSTAR_TABLE_NAMES,
        # fall back to the single table_name for backward compat.
        # When HSTAR_SCHEMA is set, table_names will be populated at
        # connection time via NeuralDB.discover_tables().
        table_names_env = os.getenv("HSTAR_TABLE_NAMES", "")
        if table_names_env:
            self.table_names = [t.strip() for t in table_names_env.split(",") if t.strip()]
        elif not self.table_names:
            self.table_names = [self.table_name]

        if not self.azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT must be set in .env or passed to Config")
        if not self.azure_deployment:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT must be set in .env or passed to Config")
        if not self.server_hostname:
            raise ValueError("DATABRICKS_SERVER_HOSTNAME must be set in .env or passed to Config")
        if not self.http_path:
            raise ValueError("DATABRICKS_HTTP_PATH must be set in .env or passed to Config")
    
    @classmethod
    def from_env(cls, model_name: str="gpt-4o") -> "Config":
        """Create configuration from environment variables."""
        load_dotenv()
        return cls.load_gpt_config(model_name)
    
    @classmethod
    def load_gpt_config(cls, model_name: str) -> "Config":
        """Load configuration with settings optimized for GPT models."""
        model_version = model_name.lower().split("-")[1] # gpt-4.1, gpt-5.4, etc.
        model_version = model_version.replace(".", "").upper() # Remove dots for easier comparison
        return cls(
            azure_endpoint=os.getenv(f"AZURE_OPENAI_{model_version}_ENDPOINT", ""),
            azure_deployment=os.getenv(f"AZURE_OPENAI_{model_version}_DEPLOYMENT", ""),
            azure_api_version=os.getenv(f"AZURE_OPENAI_{model_version}_API_VERSION", "2024-12-01-preview"),
            server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME", ""),
            http_path=os.getenv("DATABRICKS_HTTP_PATH", ""),
            table_name=os.getenv("HSTAR_TABLE_NAME", "dataset"),
            table_names=[t.strip() for t in os.getenv("HSTAR_TABLE_NAMES", "").split(",") if t.strip()],
            schema=os.getenv("HSTAR_SCHEMA", ""),
        )
