"""Prompt template for SQL-based row selection.

This stage generates SQL queries to extract relevant rows from the table(s).
Supports multi-table schemas with JOIN queries.
Output format: SQL query
"""

SYSTEM_MESSAGE = "You are an expert SQL query writer for extracting relevant data from tables. You can write queries that span multiple tables using JOINs."

INSTRUCTION = """Your task is to write a SQL query to extract the rows from the table(s) that are relevant to answer the question.

Analyze the question and write a SELECT query to retrieve the relevant rows.
Focus on filtering rows using WHERE clauses when appropriate.
When multiple tables are provided, use JOIN clauses to combine data across tables.
When relationship hints are provided, use the suggested JOIN keys to write correct JOIN conditions.

Output ONLY the SQL query without any markdown formatting or explanations."""

EXAMPLES = [
    {
        "table": """CREATE TABLE `dataset` (
  `Country` STRING,
  `Population` BIGINT
);

Sample rows:
  ('France', 67390000)
  ('Germany', 83240000)
  ('United Kingdom', 67220000)""",
        "question": "What is the population of France?",
        "output": "SELECT * FROM dataset WHERE Country = 'France'"
    },
    {
        "table": """CREATE TABLE `orders` (
  `order_id` BIGINT,
  `customer_id` BIGINT,
  `product_id` BIGINT,
  `quantity` BIGINT,
  `order_date` STRING
);

Sample rows:
  (1, 101, 501, 3, '2024-01-15')
  (2, 102, 502, 1, '2024-01-16')

CREATE TABLE `customers` (
  `customer_id` BIGINT,
  `name` STRING,
  `city` STRING,
  `country` STRING
);

Sample rows:
  (101, 'Alice', 'New York', 'USA')
  (102, 'Bob', 'London', 'UK')""",
        "question": "Which customers from the USA placed orders?",
        "output": "SELECT c.name, o.order_id, o.order_date FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE c.country = 'USA'"
    }
]
