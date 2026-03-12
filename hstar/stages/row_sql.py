"""Row SQL selection stage."""

from typing import Dict, Any, Optional
from hstar.stages.base import BaseStage
from hstar.nsql.database import NeuralDB
from hstar.prompts import row_select_sql
from hstar.utils import extract_sql_query, format_sql_results


class RowSQLStage(BaseStage):
    """
    Stage 3: Row selection using SQL query generation and execution.
    Generates and executes SQL to extract relevant rows.
    """
    
    def get_stage_name(self) -> str:
        return "ROW_SQL"
    
    def run(
        self,
        db: NeuralDB,
        question: str,
        column_desc: Optional[str] = None,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute row SQL selection.
        
        Returns:
            Dictionary with 'sql_query', 'rows', 'columns', and 'raw_output'
        """
        self.log("Selecting relevant rows using SQL generation...")
        
        # First, filter database to selected columns if available
        if previous_results and "columns" in previous_results:
            selected_cols = previous_results["columns"]
            self.log(f"Filtering to columns: {selected_cols}")
            db.filter_columns(selected_cols)
        
        # Format table for prompt
        table_str = self.prompt_builder.format_table(db)
        
        # Build prompt with examples
        prompt = self.prompt_builder.build_prompt_with_examples(
            template=row_select_sql.INSTRUCTION,
            examples=row_select_sql.EXAMPLES,
            current_table=table_str,
            current_question=question
        )
        
        # Generate SQL query
        response = self.generator.generate(
            prompt=prompt,
            system_message=row_select_sql.SYSTEM_MESSAGE,
            temperature=self.config.temperature_sql
        )
        
        # Extract and clean SQL
        sql_query = extract_sql_query(response)
        
        self.log(f"Generated SQL: {sql_query}")
        
        # Execute query
        result = db.execute_query(sql_query)
        
        if "error" in result:
            self.log(f"SQL execution error: {result['error']}")
            # Return all rows as fallback
            all_data = db.get_table_df()
            return {
                "sql_query": sql_query,
                "columns": db.get_column_names(),
                "rows": all_data.values.tolist(),
                "row_count": len(all_data),
                "raw_output": response,
                "error": result["error"],
                "stage": self.get_stage_name()
            }
        
        self.log(f"Retrieved {result['row_count']} rows")
        
        return {
            "sql_query": sql_query,
            "columns": result["header"],
            "rows": result["rows"],
            "row_count": result["row_count"],
            "raw_output": response,
            "stage": self.get_stage_name()
        }
