"""Column text refinement stage."""

from typing import Dict, Any, Optional
from hstar.stages.base import BaseStage
from hstar.nsql.database import NeuralDB
from hstar.prompts import col_select_text
from hstar.utils import extract_column_list


class ColTextStage(BaseStage):
    """
    Stage 2: Column refinement using text-based reasoning.
    Refines the column selection from ColSQLStage.
    """
    
    def get_stage_name(self) -> str:
        return "COL_TEXT"
    
    def run(
        self,
        db: NeuralDB,
        question: str,
        column_desc: Optional[str] = None,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute column text refinement.
        
        Returns:
            Dictionary with 'columns': List[str] and 'raw_output': str
        """
        self.log("Refining column selection using text reasoning...")
        
        # Get preliminary columns from previous stage
        preliminary_cols = previous_results.get("columns", db.get_column_names())
        
        # Build context — show columns from all tables in multi-table mode
        if db.is_multi_table:
            all_cols_map = db.get_all_column_names()
            context = "All available columns:\n"
            for tname, cols in all_cols_map.items():
                context += f"  {tname}: {', '.join(cols)}\n"
        else:
            all_columns = db.get_column_names()
            context = f"All available columns: {', '.join(all_columns)}\n"
        context += f"Preliminary selection: {', '.join(preliminary_cols)}"
        
        # Build prompt
        prompt = col_select_text.INSTRUCTION + "\n\n"
        
        # Add examples
        for i, example in enumerate(col_select_text.EXAMPLES):
            prompt += f"Example {i + 1}:\n"
            prompt += f"Table columns: {example['table']}\n"
            prompt += f"Question: {example['question']}\n"
            prompt += f"Preliminary: {example['preliminary']}\n"
            prompt += f"Output: {example['output']}\n\n"
        
        # Add current query
        prompt += "Now refine this selection:\n"
        prompt += f"{context}\n"
        prompt += f"Question: {question}\n"
        prompt += "Output:"
        
        # Generate response
        response = self.generator.generate(
            prompt=prompt,
            system_message=col_select_text.SYSTEM_MESSAGE,
            temperature=self.config.temperature_text
        )
        
        # Extract refined columns
        refined_columns = extract_column_list(response)
        
        if not refined_columns:
            self.log(f"Warning: Could not extract columns from output: {response}")
            # Fall back to preliminary columns
            refined_columns = preliminary_cols
        
        self.log(f"Refined columns: {refined_columns}")
        
        return {
            "columns": refined_columns,
            "raw_output": response,
            "preliminary_columns": preliminary_cols,
            "stage": self.get_stage_name()
        }
