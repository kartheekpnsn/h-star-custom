"""Row text refinement stage."""

from typing import Dict, Any, Optional
from hstar.stages.base import BaseStage
from hstar.nsql.database import NeuralDB
from hstar.prompts import row_select_text
from hstar.utils import extract_row_indices, format_sql_results


class RowTextStage(BaseStage):
    """
    Stage 4: Row refinement using text-based reasoning.
    Reviews and refines the rows selected by RowSQLStage.
    """
    
    def get_stage_name(self) -> str:
        return "ROW_TEXT"
    
    def run(
        self,
        db: NeuralDB,
        question: str,
        column_desc: Optional[str] = None,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute row text refinement.
        
        Returns:
            Dictionary with refined 'rows', 'columns', and 'raw_output'
        """
        self.log("Refining row selection using text reasoning...")
        
        # Get rows from previous stage
        if not previous_results or "rows" not in previous_results:
            self.log("Warning: No previous row results found")
            return {
                "rows": [],
                "columns": [],
                "raw_output": "",
                "stage": self.get_stage_name()
            }
        
        rows = previous_results["rows"]
        columns = previous_results["columns"]
        
        # Format rows for prompt
        rows_str = format_sql_results(columns, rows)
        
        # Build prompt
        prompt = row_select_text.INSTRUCTION + "\n\n"
        
        # Add examples
        for i, example in enumerate(row_select_text.EXAMPLES):
            prompt += f"Example {i + 1}:\n"
            prompt += f"Table:\n{example['table']}\n"
            prompt += f"Question: {example['question']}\n"
            prompt += f"Output: {example['output']}\n\n"
        
        # Add current query
        prompt += "Now review this selection:\n"
        prompt += f"Table:\n{rows_str}\n"
        prompt += f"Question: {question}\n"
        prompt += "Output:"
        
        # Generate response
        response = self.generator.generate(
            prompt=prompt,
            system_message=row_select_text.SYSTEM_MESSAGE,
            temperature=self.config.temperature_text
        )
        
        # Extract row indices or confirmation
        row_indices = extract_row_indices(response)
        
        if row_indices is None:
            # CONFIRMED - keep all rows
            self.log("Row selection confirmed")
            refined_rows = rows
        else:
            # Filter to specified indices
            self.log(f"Filtering to rows: {row_indices}")
            refined_rows = [rows[i] for i in row_indices if i < len(rows)]
        
        self.log(f"Refined to {len(refined_rows)} rows")
        
        # Update database with refined rows
        if refined_rows:
            import pandas as pd
            df = pd.DataFrame(refined_rows, columns=columns)
            db.update_table(df)
        
        return {
            "rows": refined_rows,
            "columns": columns,
            "row_count": len(refined_rows),
            "raw_output": response,
            "stage": self.get_stage_name()
        }
