"""Multi-Query Agent (MQA) — Query expansion agent using the Microsoft Agent Framework.

Given a user query the agent:
1. Tags one or more categories from config.yaml
2. Extracts time context (date / year) from the query
3. Builds an expansion prompt via PromptBuilder
4. Calls an LLM to generate multiple sub-queries

Usage:
    cd agents/mqa-agent
    uv run python starter.py
"""

import os
import sys
import json
import yaml
from typing import List
from dotenv import load_dotenv

load_dotenv()

from agent_framework import Agent, tool
from azure.identity import DefaultAzureCredential
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.devui import serve

# Resolve DB path relative to project root
_mqa_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(os.path.dirname(__file__), "..", "..")

sys.path.insert(0, _project_root)
sys.path.insert(0, _mqa_dir)

from prompt_builder import PromptBuilder
from agents.instructions.instructions import MQA_INSTRUCTIONS

_config_path = os.path.join(_mqa_dir, "config.yaml")
_builder = PromptBuilder(_config_path)

# ---------------------------------------------------------------------------
# Tool 1: get_available_categories
# ---------------------------------------------------------------------------
@tool
def get_available_categories() -> str:
    """Return the list of available query categories and their associated parameters.

    Call this first to understand which categories can be tagged to a user query.
    Each category has a name and a list of dimension parameters.
    """
    categories = []
    for item in _builder.config.get("categories", []):
        if isinstance(item, dict) and item.get("name"):
            categories.append(
                {"name": item["name"], "parameters": item.get("parameters", [])}
            )
    return json.dumps(categories, indent=2)

# ---------------------------------------------------------------------------
# Tool 2: get_parameters_for_categories
# ---------------------------------------------------------------------------
@tool
def get_parameters_for_categories(categories: List[str]) -> str:
    with open(_config_path, 'r') as f:
        config = yaml.safe_load(f)
    parameter_dict = {}
    for category in categories:
        if category not in [c["name"] for c in config["categories"]]:
            continue # In a real implementation, you might want to handle unknown categories
        for c in config["categories"]:
            if c["name"] == category:
                for param in c["parameters"]:
                    parameter_dict[param] = config["parameters"][param]
    return json.dumps(parameter_dict)

# ---------------------------------------------------------------------------
# Create agent and serve via DevUI
# ---------------------------------------------------------------------------
def main() -> None:
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    agent = Agent(
        name="mqa",
        client=client,
        instructions=MQA_INSTRUCTIONS,
        tools=[get_available_categories, get_parameters_for_categories],
    )

    print(f"Multi-Query Agent ready")
    print("Starting DevUI on http://localhost:8080 ...")
    serve(entities=[agent], port=8080, auto_open=True, instrumentation_enabled=True)


if __name__ == "__main__":
    main()
