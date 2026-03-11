"""Neural SQL database wrapper for table operations."""

import sqlite3
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any


class NeuralDB:
    """
    Neural SQL database wrapper that converts pandas DataFrames to SQLite.
    Provides query execution and result extraction capabilities.
    """
    
    def __init__(
        self, 
        table: pd.DataFrame,
        db_path: str = ":memory:",
        table_name: str = "dataset"
    ):
        """
        Initialize NeuralDB with a pandas DataFrame.
        
        Args:
            table: Input DataFrame to load into database
            db_path: Path to SQLite database (default: in-memory)
            table_name: Name for the table in the database
        """
        self.table_name = table_name
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.table_df = table.copy()
        
        # Load table into SQLite
        self._load_table(table)
        
    def _load_table(self, df: pd.DataFrame) -> None:
        """Load DataFrame into SQLite database."""
        df.to_sql(self.table_name, self.conn, index=False, if_exists="replace")
        
    def get_schema(self) -> str:
        """
        Get table schema as a string.
        
        Returns:
            String representation of table schema with column names and types
        """
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = cursor.fetchall()
        
        schema_parts = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            schema_parts.append(f"{col_name} ({col_type})")
        
        return f"Table '{self.table_name}' with columns: " + ", ".join(schema_parts)
    
    def get_create_table_sql(self) -> str:
        """
        Get CREATE TABLE statement for the table.
        
        Returns:
            SQL CREATE TABLE statement
        """
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = cursor.fetchall()
        
        col_defs = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            col_defs.append(f"  {col_name} {col_type}")
        
        return f"CREATE TABLE {self.table_name} (\n" + ",\n".join(col_defs) + "\n);"
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Dictionary with 'header' (column names) and 'rows' (query results)
            or 'error' key if execution failed
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            return {
                "header": columns,
                "rows": results,
                "row_count": len(results)
            }
        except Exception as e:
            return {
                "error": str(e),
                "query": query
            }
    
    def get_table_df(self) -> pd.DataFrame:
        """
        Get the current table as a pandas DataFrame.
        
        Returns:
            DataFrame representation of the table
        """
        return self.table_df.copy()
    
    def update_table(self, df: pd.DataFrame) -> None:
        """
        Update the table with a new DataFrame.
        
        Args:
            df: New DataFrame to replace current table
        """
        self.table_df = df.copy()
        self._load_table(df)
    
    def filter_columns(self, columns: List[str]) -> None:
        """
        Filter table to only include specified columns.
        
        Args:
            columns: List of column names to keep
        """
        # Validate columns exist
        existing_cols = set(self.table_df.columns)
        valid_cols = [col for col in columns if col in existing_cols]
        
        if not valid_cols:
            print(f"Warning: No valid columns found in {columns}")
            return
        
        # Filter DataFrame
        self.table_df = self.table_df[valid_cols]
        self._load_table(self.table_df)
    
    def filter_rows(self, row_indices: List[int]) -> None:
        """
        Filter table to only include specified row indices.
        
        Args:
            row_indices: List of row indices to keep
        """
        # Validate indices
        max_idx = len(self.table_df) - 1
        valid_indices = [idx for idx in row_indices if 0 <= idx <= max_idx]
        
        if not valid_indices:
            print(f"Warning: No valid row indices found in {row_indices}")
            return
        
        # Filter DataFrame
        self.table_df = self.table_df.iloc[valid_indices].reset_index(drop=True)
        self._load_table(self.table_df)
    
    def get_row_count(self) -> int:
        """Get number of rows in table."""
        return len(self.table_df)
    
    def get_column_names(self) -> List[str]:
        """Get list of column names."""
        return list(self.table_df.columns)
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup database connection on object destruction."""
        self.close()
