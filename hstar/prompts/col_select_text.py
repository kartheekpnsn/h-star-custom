"""Prompt template for text-based column selection refinement.

This stage refines the column selection using natural language reasoning.
Supports multi-table schemas with table-qualified column names.
Output format: refined list of column names
"""

SYSTEM_MESSAGE = "You are an expert at refining column selections for table analysis. You can work with single tables or multiple tables that may require JOINs."

INSTRUCTION = """You are given table(s), a question, and a preliminary list of selected columns.
Your task is to review these columns and output the final refined list.

Review the columns and determine if they are sufficient to answer the question.
You may keep all columns, remove unnecessary ones, or add missing ones.
When working with multiple tables, include JOIN key columns and use table-qualified names (table.column).

Output the refined column list as a comma-separated list of column names.
Example output (single table): Country, Population, Capital
Example output (multi-table): orders.customer_id, customers.name, products.product_name"""

EXAMPLES = [
    {
        "table": "Columns: Country, Capital, Population, Area_sq_km, Currency",
        "question": "What is the total population of European countries?",
        "preliminary": "Country, Population",
        "output": "Country, Population"
    },
    {
        "table": "Table orders: order_id, customer_id, product_id, quantity, order_date | Table customers: customer_id, name, city, country | Table products: product_id, product_name, category, price",
        "question": "What is the total revenue per customer?",
        "preliminary": "orders.customer_id, orders.quantity, customers.customer_id, customers.name, products.product_id, products.price",
        "output": "orders.customer_id, orders.product_id, orders.quantity, customers.customer_id, customers.name, products.product_id, products.price"
    }
]
