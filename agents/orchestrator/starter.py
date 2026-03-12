"""Sequential Workflow — MQA ➜ H-STAR pipeline via DevUI.

Flow:
    1. User submits a high-level question in the DevUI chat.
    2. The MQA Agent discovers categories & parameters, then generates
       expanded sub-queries.
    3. The H-STAR Agent answers each sub-query against the loaded dataset
       and synthesises the results.
    4. A SequentialBuilder chains MQA ➜ H-STAR so output flows automatically.

Usage:
    cd agents/orchestrator
    uv run python starter.py
"""

import os
import sys
import json
import yaml
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_orch_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.normpath(os.path.join(_orch_dir, "..", ".."))
_mqa_dir = os.path.normpath(os.path.join(_orch_dir, "..", "mqa-agent"))

sys.path.insert(0, _project_root)
sys.path.insert(0, _mqa_dir)

from agent_framework import Agent, tool
from azure.identity import DefaultAzureCredential
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.devui import serve
from agent_framework.orchestrations import SequentialBuilder

from prompt_builder import PromptBuilder
from hstar import HStar, Config
from agents.instructions.instructions import HSTAR_INSTRUCTIONS, MQA_INSTRUCTIONS

# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------
_config_path = os.path.join(_mqa_dir, "config.yaml")
_builder = PromptBuilder(_config_path)

_model_name = os.environ.get("HSTAR_MODEL_NAME", "gpt-4.1")
_db_path = os.environ.get("HSTAR_DB_PATH", "db/drug_shipments_200.db")
_db_full_path = os.path.normpath(os.path.join(_project_root, _db_path))
_column_desc_path = os.environ.get("HSTAR_COLUMN_DESC_PATH", "data/drug_shipments_200_meta.md")
_column_desc_full_path = os.path.normpath(os.path.join(_project_root, _column_desc_path))

_hstar_config = Config.from_env(model_name=_model_name)
_hstar_config.save_intermediate = False  # Don't save intermediate results for each tool call to reduce overhead
_hstar = HStar(_hstar_config)
_hstar.load_data(db_path=_db_full_path)

# Load the markdown column description if it exists
column_desc = None
if os.path.exists(_column_desc_full_path):
    with open(_column_desc_full_path, 'r') as f:
        column_desc = f.read()
        print(f"Loaded column description from {_column_desc_full_path}")
else:
    print(f"Warning: Column description file not found at {_column_desc_full_path}. Continuing without it.")

# =====================================================================
# MQA tools
# =====================================================================

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


@tool
def get_parameters_for_categories(categories: List[str]) -> str:
    """Given a list of category names, return their associated parameters and allowed values.

    Use this after selecting categories from get_available_categories to learn
    which dimension values (time_grain, geography, patient_type, etc.) are
    available for query expansion.
    """
    with open(_config_path, "r") as f:
        config = yaml.safe_load(f)
    parameter_dict: dict = {}
    valid_names = {c["name"] for c in config["categories"]}
    for category in categories:
        if category not in valid_names:
            continue
        for c in config["categories"]:
            if c["name"] == category:
                for param in c["parameters"]:
                    parameter_dict[param] = config["parameters"].get(param, [])
    return json.dumps(parameter_dict)


# =====================================================================
# H-STAR tool — parallel sub-query execution
# =====================================================================

@tool
def ask_table_questions_batch(questions: List[str]) -> str:
    """Run multiple questions through the H-STAR pipeline in parallel.

    Use this after generating sub-queries from MQA expansion. All questions
    are executed concurrently for faster results.

    Args:
        questions: A list of natural-language questions about the data.
    """
    results: dict = {}

    def _run_one(q: str) -> tuple:
        answer = _hstar.run(question=q, column_desc=column_desc, save_results=False)
        return q, answer.get("final_answer", "No answer generated.")

    with ThreadPoolExecutor(max_workers=min(len(questions), 5)) as pool:
        futures = {pool.submit(_run_one, q): q for q in questions}
        for future in as_completed(futures):
            q, answer = future.result()
            results[q] = answer

    return json.dumps(results, indent=2)

# =====================================================================
# Entrypoint
# =====================================================================
def main() -> None:
    client = AzureOpenAIResponsesClient(
        project_endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
        deployment_name=os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    # Agent A: MQA — expands user query into sub-queries
    mqa_agent = Agent(
        name="mqa",
        client=client,
        instructions=MQA_INSTRUCTIONS,
        tools=[get_available_categories, get_parameters_for_categories],
    )

    # Agent B: H-STAR — answers sub-queries against the dataset
    hstar_agent = Agent(
        name="hstar",
        client=client,
        instructions=HSTAR_INSTRUCTIONS.format(_db_path=_db_path),
        tools=[ask_table_questions_batch],
    )

    # Sequential workflow: MQA ➜ H-STAR
    workflow = SequentialBuilder(participants=[mqa_agent, hstar_agent]).build()
    sequential_agent = workflow.as_agent(name="mqa_hstar_workflow")

    print(f"All agents ready — dataset: {_db_full_path}")
    print(f"H-STAR model: {_model_name}")
    print("Starting DevUI on http://localhost:8080 ...")
    serve(
        entities=[mqa_agent, hstar_agent, workflow, sequential_agent],
        port=8080,
        auto_open=True,
        instrumentation_enabled=True,
    )


if __name__ == "__main__":
    main()
