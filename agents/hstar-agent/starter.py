"""H-STAR Agent — Table reasoning agent powered by the H-STAR pipeline.

Wraps the H-STAR pipeline as a function tool so users can ask questions
about a CSV dataset through the DevUI chat interface.

Usage:
    cd agents/hstar-agent
    uv run python starter.py
"""

import os
import sys

from dotenv import load_dotenv

# Add project root to path so hstar package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

from agent_framework import Agent, tool
from azure.identity import DefaultAzureCredential
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.devui import serve
from hstar import HStar, Config


# ---------------------------------------------------------------------------
# Initialize H-STAR pipeline once at module level
# ---------------------------------------------------------------------------
_model_name = os.environ.get("HSTAR_MODEL_NAME", "gpt-5.1")

_config = Config.from_env(model_name=_model_name)
_hstar = HStar(_config)

# Connect to Databricks
_hstar.load_data()


# ---------------------------------------------------------------------------
# Tool: ask_table_question
# ---------------------------------------------------------------------------
@tool
def ask_table_question(question: str) -> str:
    """Ask a question about the loaded CSV dataset using the H-STAR pipeline.

    The H-STAR pipeline uses a 6-stage hybrid SQL + text reasoning approach
    to analyze the table and produce an answer. It selects relevant columns,
    filters rows, and reasons over the data using both SQL and natural language.

    Args:
        question: A natural language question about the data in the CSV table.
                  Examples: "How many male passengers survived?",
                  "What was the average age of survivors?",
                  "Which class had the highest survival rate?"
    """
    results = _hstar.run(
        question=question,
        save_results=False,
    )
    return results.get("final_answer", "No answer generated.")


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------
HSTAR_INSTRUCTIONS = (
    f"You are the H-STAR Table Reasoning Agent. You help users analyze tabular data "
    f"by answering questions about the dataset '{_config.table_name}'.\n\n"
    "When a user asks a question about the data, use the ask_table_question tool "
    "to run the H-STAR pipeline and get the answer. Present the answer clearly.\n\n"
    "If the user asks a general question not related to the dataset, answer it "
    "directly without using the tool.\n\n"
    "You can handle follow-up questions — each tool call runs the full pipeline "
    "independently, so rephrase follow-ups as standalone questions when calling the tool."
)


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
        name="hstar",
        client=client,
        instructions=HSTAR_INSTRUCTIONS,
        tools=[ask_table_question],
    )

    print(f"H-STAR Agent ready — table: {_config.table_name}")
    print(f"Model: {_model_name}")
    print("Starting DevUI on http://localhost:8080 ...")
    serve(entities=[agent], port=8080, auto_open=True)


if __name__ == "__main__":
    main()
