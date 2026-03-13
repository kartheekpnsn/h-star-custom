"""SQL-based reasoning stage for final answer."""

from typing import Dict, Any, Optional
from hstar.stages.base import BaseStage
from hstar.nsql.database import NeuralDB
from hstar.prompts import sql_reason
from hstar.utils import extract_sql_query


class ReasonSQLStage(BaseStage):
    """
    Stage 5: Final reasoning using SQL query generation.
    Generates SQL to compute the final answer from extracted table.
    """
    
    def get_stage_name(self) -> str:
        return "REASON_SQL"
    
    def run(
        self,
        db: NeuralDB,
        question: str,
        column_desc: Optional[str] = None,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL-based reasoning for final answer.
        
        Returns:
            Dictionary with 'sql_query', 'sql_result', and 'raw_output'
        """
        self.log("Generating final answer using SQL reasoning...")
        
        # Format the current (filtered) table
        table_str = self.prompt_builder.format_table(db)
        
        # Build prompt with examples
        prompt = self.prompt_builder.build_prompt_with_examples(
            template=sql_reason.INSTRUCTION,
            examples=sql_reason.EXAMPLES,
            current_table=table_str,
            current_question=question
        )
        
        # Generate SQL query
        response = self.generator.generate(
            prompt=prompt,
            system_message=sql_reason.SYSTEM_MESSAGE,
            temperature=self.config.temperature_sql
        )
        
        # Extract and clean SQL
        sql_query = extract_sql_query(response)
        
        self.log(f"Generated SQL: {sql_query}")
        
        # Execute query
        result = db.execute_query(sql_query)
        
        if "error" in result:
            self.log(f"SQL execution error: {result['error']}")
            return {
                "sql_query": sql_query,
                "sql_result": None,
                "error": result["error"],
                "raw_output": response,
                "stage": self.get_stage_name()
            }
        
        # Return all result rows
        sql_result = result["rows"] if result["rows"] else []
        
        self.log(f"SQL result ({result['row_count']} rows): {sql_result}")
        
        return {
            "sql_query": sql_query,
            "sql_result": sql_result,
            "result_columns": result["header"],
            "row_count": result["row_count"],
            "raw_output": response,
            "stage": self.get_stage_name()
        }
