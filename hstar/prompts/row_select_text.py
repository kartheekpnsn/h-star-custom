"""Prompt template for text-based row selection refinement.

This stage refines row selection using natural language reasoning.
Output format: refined list of row indices or confirmation
"""

SYSTEM_MESSAGE = "You are an expert at analyzing query results and determining their relevance."

INSTRUCTION = """You are given a table, a question, and SQL query results showing selected rows.
Your task is to review these rows and confirm they are relevant to answer the question.

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
0: Alice Smith, Engineering, 75000
1: Carol White, Engineering, 68000
2: David Brown, Engineering, 85000""",
        "question": "Who works in Engineering and earns more than 70000?",
        "output": "Row indices: 0, 2"
    }
]
