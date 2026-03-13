# H-STAR Custom — Copilot Instructions

## Project overview

**H-STAR** (Hybrid SQL-Text Adaptive Reasoning) is a 6-stage LLM pipeline that answers natural-language questions about tabular data by alternating SQL-based and text-based reasoning stages. The pipeline works on CSV or SQLite datasets, using Azure OpenAI models with `DefaultAzureCredential` (no API keys).

## Quick reference

| Action | Command |
|---|---|
| Install dependencies | `uv sync` |
| Run pipeline CLI | `uv run hstar` or `uv run python run_hstar.py` |
| Run H-STAR agent | `uv run python -m agents.hstar-agent.starter` |
| Run MQA agent | `uv run python -m agents.mqa-agent.starter` |
| Convert CSV to SQLite | `uv run python hstar/sqlite/csv_to_sqlite.py data/<file>.csv` |
| Verify SQLite DB | `uv run python hstar/sqlite/verify_db.py db/<file>.db` |

No test suite exists yet. Validation is manual via pipeline runs.

## Architecture

### Pipeline stages (executed in order)

```text
Question + Table → COL_SQL → COL_TEXT → ROW_SQL → ROW_TEXT → REASON_SQL → REASON_TEXT → Answer
```

| # | Stage | Class | Purpose |
|---|---|---|---|
| 1 | COL_SQL | `ColSQLStage` | Select relevant columns via SQL reasoning |
| 2 | COL_TEXT | `ColTextStage` | Refine column selection with natural language |
| 3 | ROW_SQL | `RowSQLStage` | Generate SQL to filter relevant rows |
| 4 | ROW_TEXT | `RowTextStage` | Validate/refine row selection via NL |
| 5 | REASON_SQL | `ReasonSQLStage` | Generate final analytical SQL query |
| 6 | REASON_TEXT | `ReasonTextStage` | Synthesize natural-language answer |

### Key modules

```text
hstar/
  pipeline.py          # HStar orchestrator — load_data(), run()
  config.py            # @dataclass Config — from_env(), load_gpt_config()
  generation/
    generator.py       # Generator — Azure OpenAI wrapper with retry
    prompt_builder.py  # PromptBuilder — table formatting + few-shot assembly
  nsql/
    database.py        # NeuralDB — SQLite wrapper, column/row filtering
  stages/
    base.py            # BaseStage ABC — run(), get_stage_name()
    col_sql.py … reason_text.py  # One file per stage
  prompts/
    col_select_sql.py … text_reason.py  # SYSTEM_MESSAGE, INSTRUCTION, EXAMPLES
  utils/
    __init__.py        # Extraction helpers (extract_f_col, extract_sql_query, etc.)
  sqlite/
    csv_to_sqlite.py   # CSV→SQLite converter
agents/
  hstar-agent/starter.py   # Agent Framework wrapper around full pipeline
  mqa-agent/starter.py     # Multi-query agent for query expansion
  shared/devui.py          # AzureOpenAIResponsesClient factory + DevUI launcher
```

### Data flow

1. **Load**: `HStar.load_data()` reads CSV or SQLite into a DataFrame (cached).
2. **Per run**: A fresh in-memory `NeuralDB` copy is created (source is immutable).
3. **Each stage**: Formats the current table state → prompts the LLM → extracts structured output → optionally updates `NeuralDB`.
4. **Result**: `previous_results` dict chains through all stages; final answer in `results['final_answer']`.

## Conventions

### Naming

- **Stage classes**: `{Operation}{Method}Stage` — e.g., `ColSQLStage`, `ReasonTextStage`
- **Prompt modules**: `{operation}_{method}.py` — e.g., `col_select_sql.py`, `text_reason.py`
- **Classes**: PascalCase. **Functions**: snake_case. **Constants**: UPPER_SNAKE_CASE.

### Prompt module structure

Every file in `hstar/prompts/` exports three constants:

```python
SYSTEM_MESSAGE = "You are an expert at ..."
INSTRUCTION = """Task description with expected output format."""
EXAMPLES = [
    {"table": "CREATE TABLE ...", "question": "...", "output": "..."},
    # 2 few-shot examples per module
]
```

### Adding a new stage

1. Create `hstar/stages/<name>.py` inheriting `BaseStage`.
2. Implement `get_stage_name()` and `run(db, question, column_desc, previous_results)`.
3. Create a matching prompt module in `hstar/prompts/`.
4. Register the stage in `HStar.__init__()` inside `pipeline.py`.

### Error handling

- Stages fall back gracefully (use all columns/rows) if LLM output extraction fails.
- `Generator` retries API calls with exponential backoff (3 retries, base 2 seconds).

## Environment setup

### Required `.env` variables

```bash
AZURE_OPENAI_ENDPOINT=           # Azure OpenAI resource URL
AZURE_OPENAI_DEPLOYMENT=         # Model deployment name
AZURE_OPENAI_API_VERSION=        # API version (e.g. 2024-12-01-preview)
HSTAR_MODEL_NAME=                # Model name for Config (e.g. gpt-5.1)
HSTAR_DB_PATH=                   # SQLite DB path (e.g. db/drug_shipments_200.db)
```

### Agent Framework variables (for agents only)

```bash
AZURE_AI_PROJECT_ENDPOINT=                    # AI Foundry project endpoint
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=       # Responses API deployment
```

### Authentication

All Azure calls use `DefaultAzureCredential`. Ensure you are logged in via `az login` or have a managed identity configured.

## Domain context

The primary dataset is a pharmaceutical drug-shipment table (`drug_shipments_200.csv`) with columns covering patient info, prescriber details, payer/insurance data, drug identifiers (NDC), shipment dates, and financial assistance flags. Column descriptions live in `data/drug_shipments_200_meta.md`.

## Pitfalls

- **uv prerelease**: `agent-framework==1.0.0rc2` requires `[tool.uv] prerelease = "allow"` in `pyproject.toml`.
- **DB path**: The pipeline expects a pre-built SQLite DB at the `HSTAR_DB_PATH` path. Run `csv_to_sqlite.py` first if missing.
- **In-memory DB**: Each `run()` call copies the source table to `:memory:` — large tables increase memory usage.
- **Prompt style**: The `Config.prompt_style` setting (`create_table`, `transpose`, `text`) changes how tables appear in LLM prompts; default is `create_table`.
