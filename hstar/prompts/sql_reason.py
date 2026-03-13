"""Prompt template for SQL-based final reasoning.

This stage generates the final answer using SQL operations on the extracted table(s).
Supports multi-table schemas with JOIN queries.
"""

SYSTEM_MESSAGE = "You are an expert at writing SQL queries to derive final answers from tables. You can write complex queries with JOINs, aggregations, and subqueries across multiple tables."

INSTRUCTION = """You are given table(s) (filtered to relevant columns and rows) and a question.
Your task is to write a SQL query that produces the final answer to the question.

The query might involve:
- Simple SELECT for factual lookup
- Aggregations (COUNT, SUM, AVG, etc.) for numerical questions
- Calculations (arithmetic operations) for comparison questions
- String operations for text-based questions
- JOINs across multiple tables when the question requires data from different tables

Output ONLY the SQL query without any markdown formatting or explanations."""

EXAMPLES = [
    {
        "table": """CREATE TABLE `dataset` (
  `Country` STRING,
  `Population` BIGINT
);

Rows:
  ('France', 67390000)""",
        "question": "What is the population of France?",
        "output": "SELECT Population FROM dataset WHERE Country = 'France'"
    },
    {
        "table": """CREATE TABLE `orders` (
  `order_id` BIGINT,
  `customer_id` BIGINT,
  `product_id` BIGINT,
  `quantity` BIGINT
);

CREATE TABLE `customers` (
  `customer_id` BIGINT,
  `name` STRING,
  `country` STRING
);

CREATE TABLE `products` (
  `product_id` BIGINT,
  `product_name` STRING,
  `price` DOUBLE
);""",
        "question": "What is the total revenue per customer from the USA?",
        "output": "SELECT c.name, SUM(o.quantity * p.price) AS total_revenue FROM orders o JOIN customers c ON o.customer_id = c.customer_id JOIN products p ON o.product_id = p.product_id WHERE c.country = 'USA' GROUP BY c.name ORDER BY total_revenue DESC"
    }
]
