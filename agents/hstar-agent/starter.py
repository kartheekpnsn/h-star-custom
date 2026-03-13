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
# Pagination state
# ---------------------------------------------------------------------------
PAGE_SIZE = 5
_last_result: dict = {}  # stores last query's full SQL result for pagination


def _format_rows_page(columns: list, rows: list, page: int) -> str:
    """Format a single page of result rows as a markdown table."""
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(rows))
    page_rows = rows[start:end]

    if not page_rows or not columns:
        return "No data to display."

    header = "| " + " | ".join(str(c) for c in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = "\n".join(
        "| " + " | ".join(str(v) for v in row) + " |" for row in page_rows
    )
    table = f"{header}\n{separator}\n{body}"

    total = len(rows)
    shown_end = end
    note = f"\n\nShowing rows {start + 1}–{shown_end} of {total}."
    if shown_end < total:
        remaining = total - shown_end
        note += (
            f" There are {remaining} more row(s). "
            f"Use the **show_more_results** tool to see the next page."
        )
    return table + note


# ---------------------------------------------------------------------------
# Tool: ask_table_question
# ---------------------------------------------------------------------------
@tool
def ask_table_question(question: str) -> str:
    """Ask a question about the loaded dataset using the H-STAR pipeline.

    The H-STAR pipeline uses a 6-stage hybrid SQL + text reasoning approach
    to analyze the table and produce an answer. It selects relevant columns,
    filters rows, and reasons over the data using both SQL and natural language.

    Args:
        question: A natural language question about the data in the table.
                  Examples: "How many male passengers survived?",
                  "What was the average age of survivors?",
                  "Which class had the highest survival rate?"
    """
    global _last_result
    results = _hstar.run(
        question=question,
        save_results=False,
    )

    answer = results.get("final_answer", "No answer generated.")
    sql_rows = results.get("sql_result", [])
    columns = results.get("result_columns", [])
    row_count = results.get("row_count", 0)

    # Store full result for pagination
    _last_result = {
        "columns": columns,
        "rows": sql_rows,
        "current_page": 0,
    }

    # Append data table (first page) when there are result rows
    if sql_rows and columns:
        data_section = _format_rows_page(columns, sql_rows, page=0)
        answer += f"\n\n**Query Result ({row_count} row(s)):**\n{data_section}"

    return answer


# ---------------------------------------------------------------------------
# Tool: show_more_results
# ---------------------------------------------------------------------------
@tool
def show_more_results() -> str:
    """Show the next page of results from the most recent query.

    Use this tool when the previous answer indicated there are more rows
    available. Each call shows the next 5 rows.
    """
    global _last_result
    if not _last_result or not _last_result.get("rows"):
        return "No previous query results to paginate. Ask a question first."

    columns = _last_result["columns"]
    rows = _last_result["rows"]
    next_page = _last_result["current_page"] + 1
    start = next_page * PAGE_SIZE

    if start >= len(rows):
        return "No more rows to display. All results have been shown."

    _last_result["current_page"] = next_page
    return _format_rows_page(columns, rows, page=next_page)


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------
HSTAR_INSTRUCTIONS = (
    f"You are the H-STAR Table Reasoning Agent. You help users analyze tabular data "
    f"by answering questions about the dataset '{_config.table_name}'.\n\n"
    "When a user asks a question about the data, use the ask_table_question tool "
    "to run the H-STAR pipeline and get the answer. Present the answer clearly.\n\n"
    "Query results are paginated (5 rows at a time). If the result indicates more "
    "rows are available and the user asks to see them, use the show_more_results "
    "tool to display the next page.\n\n"
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
        tools=[ask_table_question, show_more_results],
    )

    print(f"H-STAR Agent ready — table: {_config.table_name}")
    print(f"Model: {_model_name}")
    print("Starting DevUI on http://localhost:8080 ...")
    serve(entities=[agent], port=8080, auto_open=True)


if __name__ == "__main__":
    main()
