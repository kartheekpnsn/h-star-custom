"""Prompt template for text-based row selection refinement.

This stage refines row selection using natural language reasoning.
Supports results from single-table or multi-table JOIN queries.
Output format: refined list of row indices or confirmation
"""

SYSTEM_MESSAGE = "You are an expert at analyzing query results and determining their relevance. You can work with results from single tables or JOIN queries across multiple tables."

INSTRUCTION = """You are given a table, a question, and SQL query results showing selected rows.
Your task is to review these rows and confirm they are relevant to answer the question.
The results may come from a single table or from a JOIN across multiple tables.

Analyze the rows and indicate if they are sufficient and correct for answering the question.
If rows need adjustment, specify which rows should be kept.

Output either:
- "CONFIRMED" if the rows are correct and sufficient
- "Row indices: 0, 2, 4" to specify which rows to keep (0-indexed)"""

EXAMPLES = [
    {
        "table": """Rows:
0: France, 67390000
1: Germany, 83240000""",
        "question": "What is the population of France?",
        "output": "CONFIRMED"
    },
    {
        "table": """Rows:
0: Alice, USA, Laptop, 3, 999.99
1: Alice, USA, Book, 1, 29.99
2: Bob, UK, Laptop, 2, 999.99""",
        "question": "What products did customers from the USA order?",
        "output": "Row indices: 0, 1"
    }
]
