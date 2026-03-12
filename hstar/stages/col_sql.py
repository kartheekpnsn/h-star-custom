"""Column SQL selection stage."""

from typing import Dict, Any, Optional
from hstar.stages.base import BaseStage
from hstar.nsql.database import NeuralDB
from hstar.prompts import col_select_sql
from hstar.utils import extract_f_col


class ColSQLStage(BaseStage):
    """
    Stage 1: Column selection using SQL-based reasoning.
    Identifies which columns are relevant to answer the question.
    """
    
    def get_stage_name(self) -> str:
        return "COL_SQL"
    
    def run(
        self,
        db: NeuralDB,
        question: str,
        column_desc: Optional[str] = None,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute column SQL selection.
        
        Returns:
            Dictionary with 'columns': List[str] and 'raw_output': str
        """
        self.log("Selecting relevant columns using SQL reasoning...")
        
        # Format table for prompt
        table_str = self.prompt_builder.format_table(db)
        
        # Build prompt with examples
        prompt = self.prompt_builder.build_prompt_with_examples(
            template=col_select_sql.INSTRUCTION,
            examples=col_select_sql.EXAMPLES,
            current_table=table_str,
            current_question=question
        )
        
        # Generate response
        response = self.generator.generate(
            prompt=prompt,
            system_message=col_select_sql.SYSTEM_MESSAGE,
            temperature=self.config.temperature_sql
        )
        
        # Extract columns from f_col([...]) format
        columns = extract_f_col(response)
        
        if not columns:
            self.log(f"Warning: Could not extract columns from output: {response}")
            # Fall back to all columns
            columns = db.get_column_names()
        
        self.log(f"Selected columns: {columns}")
        
        return {
            "columns": columns,
            "raw_output": response,
            "stage": self.get_stage_name()
        }
