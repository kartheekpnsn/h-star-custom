import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from prompts.simple.prompts import GENERATE_SQL_PROMPT, ADAPTIVE_REASONING_PROMPT

# Load environment variables
load_dotenv()

# Function to setup Azure OpenAI client
def setup_azure_openai_client():
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    if not endpoint or not deployment_name:
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT must be set in .env")

    # Use DefaultAzureCredential as requested
    credential = DefaultAzureCredential()

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_version=api_version,
        azure_deployment=deployment_name,
        azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token
    )
    return client, deployment_name

def load_csv_to_sqlite(csv_path: str, db_path: str = ":memory:", table_name: str = "data_table") -> sqlite3.Connection:
    """Loads a CSV file into a SQLite database."""
    print(f"Loading '{csv_path}' into SQLite database (table: '{table_name}')...")
    df = pd.read_csv(csv_path)
    
    # Create SQLite connection (in-memory by default)
    conn = sqlite3.connect(db_path)
    
    # Save dataframe to SQLite
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    print("Table loaded successfully.")
    return conn, df

def get_table_schema(conn: sqlite3.Connection, table_name: str) -> str:
    """Retrieves the schema of the specified table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    schema_parts = []
    for col in columns:
        schema_parts.append(f"{col[1]} ({col[2]})")
    
    return f"Table '{table_name}' with columns: " + ", ".join(schema_parts)

def generate_sql(client: AzureOpenAI, deployment_name: str, schema: str, question: str, table_name: str) -> str:
    """Stage 1: Table Extraction (Generate SQL from question)."""
    print("Generating SQL query using LLM...")
    prompt = GENERATE_SQL_PROMPT.format(schema=schema, question=question)
    
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a specialized SQL generation model."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=256
    )
    
    query = response.choices[0].message.content.strip()
    # Strip basic markdown if model still outputs it
    if query.startswith("```sql"):
        query = query[6:]
    if query.endswith("```"):
        query = query[:-3]
    
    print(f"Generated SQL: {query.strip()}")
    return query.strip()

def execute_sql(conn: sqlite3.Connection, query: str):
    """Executes the generated SQL query and returns the results."""
    print("Executing SQL query...")
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        print(f"Execution successful. Retrieved {len(results)} rows.")
        return columns, results
    except Exception as e:
        print(f"SQL Execution Error: {e}")
        return [], str(e)

def adaptive_reasoning(client: AzureOpenAI, deployment_name: str, question: str, sql_query: str, sql_results: str) -> str:
    """Stage 2: Adaptive Reasoning (Answer the question based on SQL execution results)."""
    print("Performing adaptive reasoning to generate the final answer...")
    
    prompt = ADAPTIVE_REASONING_PROMPT.format(
        question=question,
        sql_query=sql_query,
        sql_results=sql_results
    )

    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a specialized tabular reasoning model."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=256
    )
    
    final_answer = response.choices[0].message.content.strip()
    return final_answer

def run_hstar_pipeline(csv_path: str, question: str):
    print("=== Starting Simplified H-STAR Pipeline ===")
    
    try:
        client, deployment = setup_azure_openai_client()
    except Exception as e:
        print(f"Error setting up Azure OpenAI client: {e}")
        return

    table_name = "dataset"
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return

    # 1. Load Data
    conn, df = load_csv_to_sqlite(csv_path, table_name=table_name)
    schema = get_table_schema(conn, table_name)
    
    # 2. Table Extraction (SQL Generation)
    sql_query = generate_sql(client, deployment, schema, question, table_name)
    
    # 3. Execute query
    columns, results = execute_sql(conn, sql_query)
    
    # Format results as string for the LLM
    if isinstance(results, str):
        formatted_results = results # It's an error message
    else:
        # Convert results to a readable string format
        formatted_results = f"Columns: {', '.join(columns)}\nRows:\n"
        for row in results:
            formatted_results += f"{row}\n"
            
    # 4. Adaptive Reasoning (Final Answer)
    final_answer = adaptive_reasoning(client, deployment, question, sql_query, formatted_results)
    
    print("\n=== Pipeline Execution Complete ===")
    print(f">> Question: {question}")
    print(f">> Final Answer: {final_answer}")
    
    conn.close()

if __name__ == "__main__":
    CSV_PATH = "data/sample_table.csv"
    DEFAULT_QUESTION = "What is the population of France?"
    CSV_PATH = "data/titanic.csv"
    DEFAULT_QUESTION = "Which gender survived more on the Titanic, and what was the average age of survivors?"
    run_hstar_pipeline(CSV_PATH, DEFAULT_QUESTION)
