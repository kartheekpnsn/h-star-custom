"""Prompt template for text-based column selection refinement.

This stage refines the column selection using natural language reasoning.
Output format: refined list of column names
"""

SYSTEM_MESSAGE = "You are an expert at refining column selections for table analysis."

INSTRUCTION = """You are given a table, a question, and a preliminary list of selected columns.
Your task is to review these columns and output the final refined list.

Review the columns and determine if they are sufficient to answer the question.
You may keep all columns, remove unnecessary ones, or add missing ones.

Output the refined column list as a comma-separated list of column names.
Example output: Country, Population, Capital"""

EXAMPLES = [
    {
        "table": "Columns: Country, Capital, Population, Area_sq_km, Currency",
        "question": "What is the total population of European countries?",
        "preliminary": "Country, Population",
        "output": "Country, Population"
    },
    {
        "table": "Columns: Name, Age, Salary, Department, Join_Date, Manager",
        "question": "What is the average salary in Engineering?",
        "preliminary": "Department, Salary",
        "output": "Department, Salary"
    }
]
