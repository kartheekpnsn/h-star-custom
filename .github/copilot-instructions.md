# H-STAR Custom — Copilot Instructions

## Project overview

**H-STAR** (Hybrid SQL-Text Adaptive Reasoning) is a 6-stage LLM pipeline that answers natural-language questions about tabular data by alternating SQL-based and text-based reasoning stages. The pipeline queries tables in **Databricks SQL** (via the `databricks-sql-connector`) and uses **Azure OpenAI** models with `DefaultAzureCredential` (no API keys). It supports both single-table and multi-table (JOIN) queries, with automatic schema discovery and relationship detection.

## Quick reference

| Action | Command |
|---|---|
| Install dependencies | `uv sync` |
| Run pipeline CLI | `uv run hstar` or `uv run python run_hstar.py` |
| Run H-STAR agent | `uv run python -m agents.hstar-agent.starter` |
| Run MQA agent | `uv run python -m agents.mqa-agent.starter` |

No test suite exists yet. Validation is manual via pipeline runs.

## Architecture

### Pipeline stages (executed in order)

```text
Question + Table(s) → COL_SQL → COL_TEXT → ROW_SQL → ROW_TEXT → REASON_SQL → REASON_TEXT → Answer
```

| # | Stage | Class | Purpose |
|---|---|---|---|
| 1 | COL_SQL | `ColSQLStage` | Select relevant columns via SQL reasoning |
| 2 | COL_TEXT | `ColTextStage` | Refine column selection with natural language |
| 3 | ROW_SQL | `RowSQLStage` | Generate SQL to filter relevant rows |
| 4 | ROW_TEXT | `RowTextStage` | Validate/refine row selection via NL |
| 5 | REASON_SQL | `ReasonSQLStage` | Generate final analytical SQL query |
| 6 | REASON_TEXT | `ReasonTextStage` | Synthesize natural-language answer |

In multi-table mode, column/row filtering stages skip per-table mutation and instead let SQL stages handle filtering via JOIN queries.

### Key modules

```text
hstar/
  pipeline.py          # HStar orchestrator — load_data(), run()
  config.py            # @dataclass Config — from_env(), load_gpt_config()
  generation/
    generator.py       # Generator — Azure OpenAI wrapper with retry
    prompt_builder.py  # PromptBuilder — table formatting + few-shot assembly
  nsql/
    database.py        # NeuralDB — Databricks SQL wrapper, multi-table support
  stages/
    base.py            # BaseStage ABC — run(), get_stage_name()
    col_sql.py … reason_text.py  # One file per stage
  prompts/
    col_select_sql.py … text_reason.py  # SYSTEM_MESSAGE, INSTRUCTION, EXAMPLES
  utils/
    __init__.py        # Extraction helpers (extract_f_col, extract_sql_query, etc.)
  sqlite/
    csv_to_sqlite.py   # Legacy CSV→SQLite converter (not used with Databricks)
agents/
  hstar-agent/starter.py   # Agent Framework wrapper around full pipeline
  mqa-agent/starter.py     # Multi-query agent for query expansion
  shared/devui.py          # AzureOpenAIResponsesClient factory + DevUI launcher
```

### Data flow

1. **Connect**: `HStar.load_data()` establishes a Databricks SQL connection via Azure AD token authentication. When `HSTAR_SCHEMA` is configured, it auto-discovers all tables in the schema.
2. **Per run**: A `NeuralDB` instance is created with the connection and table name(s). In multi-table mode, it detects relationships (candidate JOIN keys) across tables by matching column names and types.
3. **Each stage**: Formats table schema(s) and relationship hints → prompts the LLM → extracts structured output → optionally updates the query context.
4. **Result**: `previous_results` dict chains through all stages; final answer in `results['final_answer']`.

### Multi-table support

The pipeline supports querying across multiple tables with JOINs:

- **Table resolution priority**: explicit `HSTAR_TABLE_NAMES` → schema auto-discovery via `HSTAR_SCHEMA` → single `HSTAR_TABLE_NAME`.
- **Schema auto-discovery**: `NeuralDB.discover_tables()` runs `SHOW TABLES IN <schema>` against Databricks to find all available tables.
- **Relationship detection**: `NeuralDB.detect_relationships()` compares columns across all table pairs by name and type, identifying candidate JOIN keys. Compatible types (exact match or both numeric) are treated as joinable.
- **Relationship hints**: `NeuralDB.get_relationship_hints()` formats detected relationships as text (e.g., `left.col → right.col`) and `PromptBuilder.format_tables()` appends them after the CREATE TABLE schemas so the LLM can generate correct JOIN conditions.
- **Column references**: In multi-table mode, `extract_f_col()` and `parse_qualified_column()` handle `table.column` qualified names.

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

SQL prompt INSTRUCTIONs reference relationship hints for JOIN key guidance.

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
HSTAR_MODEL_NAME=                # Model name for Config (e.g. gpt-5.4)
DATABRICKS_SERVER_HOSTNAME=      # Databricks workspace hostname
DATABRICKS_HTTP_PATH=            # Databricks SQL warehouse HTTP path
```

### Table configuration (choose one)

```bash
HSTAR_TABLE_NAME=                # Single fully qualified table (catalog.schema.table)
HSTAR_TABLE_NAMES=               # Comma-separated list of fully qualified table names
HSTAR_SCHEMA=                    # catalog.schema for auto-discovery (e.g. hive_metastore.piiq)
```

### Optional variables

```bash
HSTAR_COLUMN_DESC_PATH=          # Path to column description markdown (default: data/drug_shipments_200_meta.md)
```

### Agent Framework variables (for agents only)

```bash
AZURE_AI_PROJECT_ENDPOINT=                    # AI Foundry project endpoint
AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME=       # Responses API deployment
```

### Authentication

All Azure calls use `DefaultAzureCredential`. Databricks connections use Azure AD token authentication (scope `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default`). Ensure you are logged in via `az login` or have a managed identity configured.

## Domain context

The primary dataset consists of tables in a Databricks Hive Metastore schema (e.g., `hive_metastore.piiq`). The pipeline auto-discovers all tables when `HSTAR_SCHEMA` is set. Column descriptions can be provided via a markdown file at `HSTAR_COLUMN_DESC_PATH`.

## Pitfalls

- **uv prerelease**: `agent-framework==1.0.0rc2` requires `[tool.uv] prerelease = "allow"` in `pyproject.toml`.
- **Databricks connection**: Requires `DATABRICKS_SERVER_HOSTNAME` and `DATABRICKS_HTTP_PATH` environment variables. The connection uses Azure AD tokens, not personal access tokens.
- **Schema discovery**: When `HSTAR_SCHEMA` is set and `HSTAR_TABLE_NAMES` is not, the pipeline discovers tables at connection time. Ensure the schema path is correct (e.g., `hive_metastore.piiq`).
- **No formal FKs**: Hive Metastore does not enforce foreign key constraints. Relationship detection uses a name-and-type matching heuristic — columns with the same name and compatible types across tables are treated as candidate JOIN keys.
- **Multi-table filtering**: In multi-table mode, column and row filtering stages skip per-table mutation. The SQL reasoning stages handle filtering via JOIN queries.
- **Prompt style**: The `Config.prompt_style` setting (`create_table`, `transpose`, `text`) changes how tables appear in LLM prompts; default is `create_table`.
