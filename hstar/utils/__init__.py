"""Utility functions for H-STAR pipeline."""

import re
import json
from typing import List, Dict, Any, Optional, Tuple


def extract_f_col(text: str) -> List[str]:
    """
    Extract column names from f_col([...]) format.
    Supports both unqualified (column) and table-qualified (table.column) names.
    
    Args:
        text: Generated text containing f_col marker
        
    Returns:
        List of column names (may include table.column format)
    """
    # Look for f_col([...]) pattern
    pattern = r'f_col\(\[(.*?)\]\)'
    match = re.search(pattern, text)
    
    if match:
        content = match.group(1)
        # Split by comma and clean whitespace
        columns = [col.strip().strip('"').strip("'") for col in content.split(',')]
        return [col for col in columns if col]  # Filter empty strings
    
    return []


def parse_qualified_column(col: str) -> tuple:
    """
    Split a potentially table-qualified column name.

    Args:
        col: Column name, optionally table-qualified (e.g., "table.column")

    Returns:
        Tuple of (table_name_or_None, column_name)
    """
    if "." in col:
        parts = col.rsplit(".", 1)
        return (parts[0], parts[1])
    return (None, col)


def extract_f_row(text: str) -> List[int]:
    """
    Extract row indices from f_row([...]) format.
    
    Args:
        text: Generated text containing f_row marker
        
    Returns:
        List of row indices
    """
    # Look for f_row([...]) pattern
    pattern = r'f_row\(\[(.*?)\]\)'
    match = re.search(pattern, text)
    
    if match:
        content = match.group(1)
        # Extract integers
        try:
            indices = [int(idx.strip()) for idx in content.split(',') if idx.strip()]
            return indices
        except ValueError:
            return []
    
    return []


def extract_sql_query(text: str) -> str:
    """
    Extract SQL query from generated text, removing markdown formatting.
    
    Args:
        text: Generated text potentially containing SQL
        
    Returns:
        Clean SQL query
    """
    # Remove markdown SQL code blocks
    text = text.strip()
    
    if text.startswith("```sql"):
        text = text[6:]
    elif text.startswith("```"):
        text = text[3:]
        
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()


def extract_column_list(text: str) -> List[str]:
    """
    Extract comma-separated column names from text.
    
    Args:
        text: Generated text with column names
        
    Returns:
        List of column names
    """
    # Clean up the text
    text = text.strip()
    
    # Remove common prefixes
    text = re.sub(r'^(refined columns?:|final columns?:|columns?:)\s*', '', text, flags=re.IGNORECASE)
    
    # Split by comma and clean
    columns = [col.strip().strip('"').strip("'") for col in text.split(',')]
    return [col for col in columns if col]


def extract_row_indices(text: str) -> Optional[List[int]]:
    """
    Extract row indices from text refinement output.
    
    Args:
        text: Generated text with row indices or CONFIRMED
        
    Returns:
        List of row indices, or None if confirmed
    """
    text = text.strip().upper()
    
    if "CONFIRMED" in text:
        return None  # None means keep all current rows
    
    # Look for "Row indices: 0, 2, 4" pattern
    pattern = r'(?:row\s+)?indices?:\s*([\d,\s]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        indices_str = match.group(1)
        try:
            indices = [int(idx.strip()) for idx in indices_str.split(',') if idx.strip()]
            return indices
        except ValueError:
            return None
    
    return None


def format_sql_results(columns: List[str], rows: List[Tuple]) -> str:
    """
    Format SQL query results as a readable string.
    
    Args:
        columns: Column names
        rows: Query result rows
        
    Returns:
        Formatted string representation
    """
    if not rows:
        return "No results"
    
    result = f"Columns: {', '.join(columns)}\n"
    result += f"Rows ({len(rows)} total):\n"
    
    for i, row in enumerate(rows):
        values = ", ".join([str(v) for v in row])
        result += f"  {i}: {values}\n"
    
    return result


def save_stage_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save stage results to JSON file.
    
    Args:
        results: Dictionary of results to save
        output_path: Path to output JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def load_stage_results(input_path: str) -> Dict[str, Any]:
    """
    Load stage results from JSON file.
    
    Args:
        input_path: Path to input JSON file
        
    Returns:
        Dictionary of loaded results
    """
    with open(input_path, 'r') as f:
        return json.load(f)


def normalize_sql(sql: str) -> str:
    """
    Normalize SQL query for consistency.
    
    Args:
        sql: Raw SQL query
        
    Returns:
        Normalized SQL query
    """
    # Remove extra whitespace
    sql = ' '.join(sql.split())
    
    # Ensure ends with semicolon
    if not sql.endswith(';'):
        sql += ';'
    
    return sql


def truncate_table_for_prompt(
    columns: List[str],
    rows: List[Tuple],
    max_rows: int = 50
) -> List[Tuple]:
    """
    Truncate table rows to fit within token limits.
    
    Args:
        columns: Column names
        rows: Table rows
        max_rows: Maximum number of rows to keep
        
    Returns:
        Truncated list of rows
    """
    if len(rows) <= max_rows:
        return rows
    
    # Keep first rows (most important context usually at top)
    return rows[:max_rows]
