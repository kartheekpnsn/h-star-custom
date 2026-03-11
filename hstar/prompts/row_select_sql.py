"""Prompt template for SQL-based row selection.

This stage generates SQL queries to extract relevant rows from the table.
Output format: f_row([row_id1, row_id2, ...]) based on SQL execution
"""

SYSTEM_MESSAGE = "You are an expert SQL query writer for extracting relevant data from tables."

INSTRUCTION = """Your task is to write a SQL query to extract the rows from the table that are relevant to answer the question.

Analyze the question and write a SELECT query to retrieve the relevant rows.
Focus on filtering rows using WHERE clauses when appropriate.

Output ONLY the SQL query without any markdown formatting or explanations."""

EXAMPLES = [
    {
        "table": """CREATE TABLE dataset (
  Country TEXT,
  Population INTEGER
);

Sample rows:
  ('France', 67390000)
  ('Germany', 83240000)
  ('United Kingdom', 67220000)""",
        "question": "What is the population of France?",
        "output": "SELECT * FROM dataset WHERE Country = 'France'"
    },
    {
        "table": """CREATE TABLE dataset (
  Name TEXT,
  Department TEXT,
  Salary INTEGER
);

Sample rows:
  ('Alice Smith', 'Engineering', 75000)
  ('Bob Johnson', 'Sales', 95000)
  ('Carol White', 'Engineering', 68000)""",
        "question": "Who works in Engineering and earns more than 70000?",
        "output": "SELECT * FROM dataset WHERE Department = 'Engineering' AND Salary > 70000"
    }
]
