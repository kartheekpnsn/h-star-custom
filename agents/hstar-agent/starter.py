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
from agents.instructions.instructions import HSTAR_INSTRUCTIONS


# ---------------------------------------------------------------------------
# Initialize H-STAR pipeline once at module level
# ---------------------------------------------------------------------------
_model_name = os.environ.get("HSTAR_MODEL_NAME", "gpt-5.1")
_db_path = os.environ.get("HSTAR_DB_PATH", "db/drug_shipments_200.db")
_column_desc_path = os.environ.get("HSTAR_COLUMN_DESC_PATH", "data/drug_shipments_200_meta.md")

# Resolve DB path relative to project root
_project_root = os.path.join(os.path.dirname(__file__), "..", "..")
_db_full_path = os.path.normpath(os.path.join(_project_root, _db_path))
_column_desc_full_path = os.path.normpath(os.path.join(_project_root, _column_desc_path))

# Load the markdown column description if it exists
column_desc = None
if os.path.exists(_column_desc_full_path):
    with open(_column_desc_full_path, 'r') as f:
        column_desc = f.read()
        print(f"Loaded column description from {_column_desc_full_path}")
else:
    print(f"Warning: Column description file not found at {_column_desc_full_path}. Continuing without it.")


_config = Config.from_env(model_name=_model_name)
_config.save_intermediate = False  # Don't save intermediate results for each tool call to reduce overhead
_hstar = HStar(_config)

# Load data once from DB
_hstar.load_data(db_path=_db_full_path)


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
        column_desc=column_desc,
        save_results=False,
    )
    return results.get("final_answer", "No answer generated.")

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
        instructions=HSTAR_INSTRUCTIONS.format(_db_path=_db_path),
        tools=[ask_table_question],
    )

    print(f"H-STAR Agent ready — dataset: {_db_full_path}")
    print(f"Model: {_model_name}")
    print("Starting DevUI on http://localhost:8080 ...")
    serve(entities=[agent], port=8080, auto_open=True, instrumentation_enabled=True)


if __name__ == "__main__":
    main()
