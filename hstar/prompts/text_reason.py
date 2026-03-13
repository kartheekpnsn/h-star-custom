"""Prompt template for text-based final reasoning.

This stage produces the final natural language answer based on all previous results.
Supports results from single-table queries or multi-table JOIN queries.
"""

SYSTEM_MESSAGE = "You are an expert at synthesizing information from tables to answer questions. You can interpret results from single tables or complex JOIN queries across multiple tables."

INSTRUCTION = """You are given:
1. Original question
2. Extracted table data (relevant columns and rows)
3. SQL query result that was executed

Your task is to provide a clear, natural language answer to the question based on this information.
The data may come from a single table or from JOIN queries across multiple tables.

Guidelines:
- Be concise and direct
- Include relevant numbers or facts from the data
- If the query produced a calculation, explain what it represents
- If the query involved JOINs, synthesize the combined information naturally
- If data is missing or insufficient, state that clearly

Output only the final answer in natural language."""

EXAMPLES = [
    {
        "question": "What is the population of France?",
        "sql_result": "67390000",
        "output": "The population of France is 67,390,000."
    },
    {
        "question": "What is the total revenue per customer from the USA?",
        "sql_result": "Alice, 3029.96\nCarol, 1999.98",
        "output": "The total revenue per customer from the USA is: Alice with $3,029.96 and Carol with $1,999.98."
    }
]
