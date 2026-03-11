"""Text-based reasoning stage for final answer."""

from typing import Dict, Any, Optional
from hstar.stages.base import BaseStage
from hstar.nsql.database import NeuralDB
from hstar.prompts import text_reason


class ReasonTextStage(BaseStage):
    """
    Stage 6: Final reasoning using text-based synthesis.
    Produces natural language answer based on all previous results.
    """
    
    def get_stage_name(self) -> str:
        return "REASON_TEXT"
    
    def run(
        self,
        db: NeuralDB,
        question: str,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute text-based reasoning for final answer.
        
        Returns:
            Dictionary with 'final_answer' and 'raw_output'
        """
        self.log("Generating final natural language answer...")
        
        # Get SQL result from previous stage
        sql_result = None
        sql_query = None
        if previous_results:
            sql_result = previous_results.get("sql_result")
            sql_query = previous_results.get("sql_query")
        
        # Format context
        context = f"SQL Query Executed: {sql_query}\n"
        context += f"SQL Result: {sql_result}\n"
        
        # Get table summary
        table_str = self.prompt_builder.format_table(db)
        context += f"\nExtracted Table:\n{table_str}"
        
        # Build prompt
        prompt = text_reason.INSTRUCTION + "\n\n"
        
        # Add examples
        for i, example in enumerate(text_reason.EXAMPLES):
            prompt += f"Example {i + 1}:\n"
            prompt += f"Question: {example['question']}\n"
            prompt += f"SQL Result: {example['sql_result']}\n"
            prompt += f"Output: {example['output']}\n\n"
        
        # Add current query
        prompt += "Now answer this:\n"
        prompt += f"Question: {question}\n"
        prompt += f"{context}\n"
        prompt += "Output:"
        
        # Generate final answer
        response = self.generator.generate(
            prompt=prompt,
            system_message=text_reason.SYSTEM_MESSAGE,
            temperature=self.config.temperature_text
        )
        
        self.log(f"Final answer: {response}")
        
        return {
            "final_answer": response,
            "raw_output": response,
            "sql_result": sql_result,
            "sql_query": sql_query,
            "stage": self.get_stage_name()
        }
