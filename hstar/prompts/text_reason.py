"""Prompt template for text-based final reasoning.

This stage produces the final natural language answer based on all previous results.
"""

SYSTEM_MESSAGE = "You are an expert at synthesizing information from tables to answer questions."

INSTRUCTION = """You are given:
1. Original question
2. Extracted table data (relevant columns and rows)
3. SQL query result that was executed

Your task is to provide a clear, natural language answer to the question based on this information.

Guidelines:
- Be concise and direct
- Include relevant numbers or facts from the data
- If the query produced a calculation, explain what it represents
- If data is missing or insufficient, state that clearly

Output only the final answer in natural language."""

EXAMPLES = [
    {
        "question": "What is the population of France?",
        "sql_result": "67390000",
        "output": "The population of France is 67,390,000."
    },
    {
        "question": "What is the population difference between Germany and France?",
        "sql_result": "15850000",
        "output": "The population difference between Germany and France is 15,850,000, with Germany having the larger population."
    }
]
