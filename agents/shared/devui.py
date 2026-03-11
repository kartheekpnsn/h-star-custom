"""Shared DevUI helpers for the AETHER agent challenges."""

import os

from azure.identity import DefaultAzureCredential
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.devui import serve


def create_client() -> AzureOpenAIResponsesClient:
    """Create the standard Azure OpenAI client from environment variables."""
    return AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )


def launch(entities: list, port: int = 8080) -> None:
    """Print a startup banner and launch the DevUI."""
    print(f"Starting AETHER Sentry DevUI on http://localhost:{port} ...")
    serve(entities=entities, port=port, auto_open=True)
