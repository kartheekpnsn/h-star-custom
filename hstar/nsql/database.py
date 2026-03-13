"""Neural SQL database wrapper for Databricks."""

import pandas as pd
from typing import Dict, List, Any

from databricks import sql as databricks_sql

# Map pandas dtypes to Spark SQL types
DTYPE_MAP = {
    "object": "STRING",
    "int64": "BIGINT",
    "float64": "DOUBLE",
    "bool": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
}


class NeuralDB:
    """
    Neural SQL database wrapper that queries tables in Databricks.
    Provides query execution and result extraction capabilities.
    Supports single-table and multi-table (JOIN) modes.
    """

    def __init__(
        self,
        connection: databricks_sql.client.Connection,
        table_name: str = "dataset",
        table_names: list[str] | None = None,
    ):
        """
        Initialize NeuralDB with a Databricks SQL connection.

        Args:
            connection: Pre-established Databricks SQL connection
            table_name: Fully qualified table name (catalog.schema.table)
            table_names: List of fully qualified table names for multi-table mode
        """
        self.table_name = table_name
        self.table_names = table_names or [table_name]
        self._connection = connection
        self._cursor = connection.cursor()
        self._current_view = table_name
        self._column_cache: list[dict[str, str]] | None = None
        self._column_caches: dict[str, list[dict[str, str]]] = {}
        # Short name for temporary views (Spark requires single-part names)
        self._short_name = table_name.rsplit(".", 1)[-1]

    @property
    def is_multi_table(self) -> bool:
        """Whether the database is configured for multi-table mode."""
        return len(self.table_names) > 1

    @staticmethod
    def discover_tables(
        cursor,
        schema: str,
    ) -> List[str]:
        """Discover all tables in a Databricks catalog.schema.

        Runs ``SHOW TABLES IN <schema>`` and returns fully qualified
        table names (``catalog.schema.table``).

        Args:
            cursor: Active Databricks SQL cursor.
            schema: Fully qualified schema name (e.g. ``hive_metastore.piiq``).

        Returns:
            Sorted list of fully qualified table names.
        """
        cursor.execute(f"SHOW TABLES IN {schema}")
        rows = cursor.fetchall()
        # SHOW TABLES returns (database, tableName, isTemporary)
        tables = [
            f"{schema}.{row[1]}"
            for row in rows
            if not row[2]  # exclude temporary tables/views
        ]
        return sorted(tables)

    def _invalidate_cache(self) -> None:
        """Invalidate the column cache."""
        self._column_cache = None

    def _describe_table(self) -> list[dict[str, str]]:
        """Get column metadata via DESCRIBE TABLE, using cache when available."""
        if self._column_cache is not None:
            return self._column_cache

        self._cursor.execute(f"DESCRIBE TABLE {self._current_view}")
        rows = self._cursor.fetchall()

        self._column_cache = [
            {"name": row[0], "type": row[1], "comment": row[2] or ""}
            for row in rows
            if not str(row[0]).startswith("#")
        ]
        return self._column_cache

    def get_schema(self) -> str:
        """Get table schema as a formatted string."""
        columns = self._describe_table()
        schema_parts = [f"{col['name']} ({col['type']})" for col in columns]
        return f"Table '{self.table_name}' with columns: " + ", ".join(schema_parts)

    def get_create_table_sql(self) -> str:
        """Get CREATE TABLE statement for the table."""
        columns = self._describe_table()
        col_defs = [f"  `{col['name']}` {col['type']}" for col in columns]
        return f"CREATE TABLE `{self.table_name}` (\n" + ",\n".join(col_defs) + "\n);"

    def get_column_names(self) -> List[str]:
        """Get list of column names."""
        columns = self._describe_table()
        return [col["name"] for col in columns]

    def _describe_named_table(self, name: str) -> list[dict[str, str]]:
        """Get column metadata for a specific table, with caching."""
        if name in self._column_caches:
            return self._column_caches[name]

        self._cursor.execute(f"DESCRIBE TABLE {name}")
        rows = self._cursor.fetchall()

        cols = [
            {"name": row[0], "type": row[1], "comment": row[2] or ""}
            for row in rows
            if not str(row[0]).startswith("#")
        ]
        self._column_caches[name] = cols
        return cols

    def get_create_table_sql_for(self, name: str) -> str:
        """Get CREATE TABLE statement for a specific table."""
        columns = self._describe_named_table(name)
        col_defs = [f"  `{col['name']}` {col['type']}" for col in columns]
        return f"CREATE TABLE `{name}` (\n" + ",\n".join(col_defs) + "\n);"

    def get_all_create_table_sql(self) -> str:
        """Get CREATE TABLE statements for all tables, separated by blank lines."""
        return "\n\n".join(
            self.get_create_table_sql_for(name) for name in self.table_names
        )

    def get_all_column_names(self) -> Dict[str, List[str]]:
        """Get column names for all tables as {table_name: [col_names]}."""
        return {
            name: [col["name"] for col in self._describe_named_table(name)]
            for name in self.table_names
        }

    def get_sample_rows(self, name: str, limit: int = 5) -> tuple[List[str], List[list]]:
        """Get sample rows from a specific table.

        Returns:
            Tuple of (column_names, rows)
        """
        self._cursor.execute(f"SELECT * FROM {name} LIMIT {int(limit)}")
        rows = self._cursor.fetchall()
        columns = [desc[0] for desc in self._cursor.description]
        return columns, [list(r) for r in rows]

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results.

        Args:
            query: SQL query to execute

        Returns:
            Dictionary with 'header', 'rows', 'row_count' or 'error'
        """
        try:
            self._cursor.execute(query)
            results = self._cursor.fetchall()
            columns = (
                [desc[0] for desc in self._cursor.description]
                if self._cursor.description
                else []
            )
            return {
                "header": columns,
                "rows": [list(r) for r in results],
                "row_count": len(results),
            }
        except Exception as e:
            return {"error": str(e), "query": query}

    def get_table_df(self, max_rows: int = 50) -> pd.DataFrame:
        """
        Get the current table as a pandas DataFrame.

        Args:
            max_rows: Maximum number of rows to retrieve

        Returns:
            DataFrame representation of the table
        """
        self._cursor.execute(
            f"SELECT * FROM {self._current_view} LIMIT {int(max_rows)}"
        )
        rows = self._cursor.fetchall()
        columns = [desc[0] for desc in self._cursor.description]
        return pd.DataFrame([list(r) for r in rows], columns=columns)

    def filter_columns(self, columns: List[str]) -> None:
        """
        Filter table to only include specified columns.

        Args:
            columns: List of column names to keep
        """
        existing = set(self.get_column_names())
        valid_cols = [col for col in columns if col in existing]

        if not valid_cols:
            print(f"Warning: No valid columns found in {columns}")
            return

        col_list = ", ".join(f"`{c}`" for c in valid_cols)
        view_name = f"{self._short_name}_filtered"
        self._cursor.execute(
            f"CREATE OR REPLACE TEMPORARY VIEW {view_name} "
            f"AS SELECT {col_list} FROM {self._current_view}"
        )
        self._current_view = view_name
        self._invalidate_cache()

    def update_table(self, df: pd.DataFrame) -> None:
        """
        Update the table with a new DataFrame via a VALUES-based temporary view.

        Args:
            df: New DataFrame to replace current table
        """
        if df.empty:
            return

        col_defs = []
        for col_name in df.columns:
            dtype_str = str(df[col_name].dtype)
            spark_type = DTYPE_MAP.get(dtype_str, "STRING")
            col_defs.append(f"`{col_name}` {spark_type}")

        value_rows = []
        for _, row in df.iterrows():
            values = []
            for val in row:
                if pd.isna(val):
                    values.append("NULL")
                elif isinstance(val, bool):
                    values.append("TRUE" if val else "FALSE")
                elif isinstance(val, str):
                    escaped = val.replace("'", "''")
                    values.append(f"'{escaped}'")
                else:
                    values.append(str(val))
            value_rows.append(f"({', '.join(values)})")

        view_name = f"{self._short_name}_refined"
        col_def_str = ", ".join(col_defs)
        values_str = ", ".join(value_rows)

        self._cursor.execute(
            f"CREATE OR REPLACE TEMPORARY VIEW {view_name}({col_def_str}) "
            f"AS SELECT * FROM VALUES {values_str}"
        )
        self._current_view = view_name
        self._invalidate_cache()

    def filter_rows(self, row_indices: List[int]) -> None:
        """Filter table to only include specified row indices (stub — unused)."""

    def get_row_count(self) -> int:
        """Get number of rows in table."""
        self._cursor.execute(f"SELECT COUNT(*) FROM {self._current_view}")
        result = self._cursor.fetchone()
        return result[0]

    def close(self) -> None:
        """Close the cursor (connection is managed by the caller)."""
        if self._cursor:
            self._cursor.close()
