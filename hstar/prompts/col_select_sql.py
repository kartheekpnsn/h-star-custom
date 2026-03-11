"""Prompt template for SQL-based column selection.

This stage identifies which columns are relevant to answer the question.
Output format: f_col([column1, column2, ...])
"""

SYSTEM_MESSAGE = "You are an expert at analyzing tables and identifying relevant columns for answering questions."

INSTRUCTION = """Your task is to identify which columns from the table are relevant to answer the given question.

Analyze the question and the table schema, then output ONLY the relevant column names in this exact format:
f_col([column1, column2, ...])

Include only the columns that are necessary to answer the question. Do not include unnecessary columns."""

# Few-shot examples
EXAMPLES = [
    {
        "table": """CREATE TABLE dataset (
  Country TEXT,
  Capital TEXT,
  Population INTEGER,
  Area_sq_km INTEGER,
  Currency TEXT
);

Sample rows:
  ('France', 'Paris', 67390000, 551695, 'Euro')
  ('Germany', 'Berlin', 83240000, 357022, 'Euro')
  ('United Kingdom', 'London', 67220000, 242495, 'Pound Sterling')""",
        "question": "What is the population of France?",
        "output": "f_col([Country, Population])"
    },
    {
        "table": """CREATE TABLE dataset (
  Name TEXT,
  Age INTEGER,
  Salary INTEGER,
  Department TEXT,
  Join_Date TEXT
);

Sample rows:
  ('Alice Smith', 32, 75000, 'Engineering', '2019-03-15')
  ('Bob Johnson', 45, 95000, 'Sales', '2015-07-22')
  ('Carol White', 28, 68000, 'Marketing', '2020-11-03')""",
        "question": "Who works in the Engineering department?",
        "output": "f_col([Name, Department])"
    }
]
