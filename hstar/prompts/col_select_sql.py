"""Prompt template for SQL-based column selection.

This stage identifies which columns are relevant to answer the question.
Output format: f_col([column1, column2, ...])
Supports multi-table schemas with table-qualified column names.
"""

SYSTEM_MESSAGE = "You are an expert at analyzing table schemas and identifying relevant columns for answering questions. You can work with single tables or multiple tables that may require JOINs."

INSTRUCTION = """Your task is to identify which columns from the table(s) are relevant to answer the given question.

Analyze the question and the table schema(s), then output ONLY the relevant column names in this exact format:
f_col([column1, column2, ...])

When multiple tables are provided, use table-qualified column names:
f_col([table_name.column1, table_name.column2, other_table.column3])

Include only the columns that are necessary to answer the question. Do not include unnecessary columns.
If the question requires data from multiple tables, include the JOIN key columns as well.
When relationship hints are provided, use them to identify the correct JOIN key columns."""

# Few-shot examples
EXAMPLES = [
    {
        "table": """CREATE TABLE `dataset` (
  `Country` STRING,
  `Capital` STRING,
  `Population` BIGINT,
  `Area_sq_km` BIGINT,
  `Currency` STRING
);

Sample rows:
  ('France', 'Paris', 67390000, 551695, 'Euro')
  ('Germany', 'Berlin', 83240000, 357022, 'Euro')
  ('United Kingdom', 'London', 67220000, 242495, 'Pound Sterling')""",
        "question": "What is the population of France?",
        "output": "f_col([Country, Population])"
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
  (102, 'Bob', 'London', 'UK')

CREATE TABLE `products` (
  `product_id` BIGINT,
  `product_name` STRING,
  `category` STRING,
  `price` DOUBLE
);

Sample rows:
  (501, 'Laptop', 'Electronics', 999.99)
  (502, 'Book', 'Education', 29.99)""",
        "question": "What products did customers from the USA order?",
        "output": "f_col([orders.customer_id, orders.product_id, customers.customer_id, customers.name, customers.country, products.product_id, products.product_name])"
    }
]
