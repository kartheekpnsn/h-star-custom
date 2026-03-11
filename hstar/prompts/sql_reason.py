"""Prompt template for SQL-based final reasoning.

This stage generates the final answer using SQL operations on the extracted table.
"""

SYSTEM_MESSAGE = "You are an expert at writing SQL queries to derive final answers from tables."

INSTRUCTION = """You are given a table (filtered to relevant columns and rows) and a question.
Your task is to write a SQL query that produces the final answer to the question.

The query might involve:
- Simple SELECT for factual lookup
- Aggregations (COUNT, SUM, AVG, etc.) for numerical questions
- Calculations (arithmetic operations) for comparison questions
- String operations for text-based questions

Output ONLY the SQL query without any markdown formatting or explanations."""

EXAMPLES = [
    {
        "table": """CREATE TABLE dataset (
  Country TEXT,
  Population INTEGER
);

Rows:
  ('France', 67390000)""",
        "question": "What is the population of France?",
        "output": "SELECT Population FROM dataset WHERE Country = 'France'"
    },
    {
        "table": """CREATE TABLE dataset (
  Country TEXT,
  Population INTEGER
);

Rows:
  ('France', 67390000)
  ('Germany', 83240000)""",
        "question": "What is the population difference between Germany and France?",
        "output": "SELECT (SELECT Population FROM dataset WHERE Country = 'Germany') - (SELECT Population FROM dataset WHERE Country = 'France') AS difference"
    }
]
