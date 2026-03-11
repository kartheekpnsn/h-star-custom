"""Prompt builder for constructing few-shot prompts with tables."""

import pandas as pd
from typing import List, Optional, Dict, Any
from hstar.nsql.database import NeuralDB


class PromptBuilder:
    """
    Builds prompts for different stages of the H-STAR pipeline.
    Supports multiple table formatting styles and few-shot examples.
    """
    
    def __init__(self, prompt_style: str = "create_table", max_rows: int = 50):
        """
        Initialize prompt builder.
        
        Args:
            prompt_style: Table formatting style ('create_table', 'transpose', 'text')
            max_rows: Maximum number of table rows to include
        """
        self.prompt_style = prompt_style
        self.max_rows = max_rows
    
    def format_table(self, db: NeuralDB) -> str:
        """
        Format table according to prompt style.
        
        Args:
            db: NeuralDB instance containing the table
            
        Returns:
            Formatted table string
        """
        df = db.get_table_df()
        
        # Truncate if too many rows
        if len(df) > self.max_rows:
            df = df.head(self.max_rows)
        
        if self.prompt_style == "create_table":
            return self._format_create_table(db, df)
        elif self.prompt_style == "transpose":
            return self._format_transpose(df)
        elif self.prompt_style == "text":
            return self._format_text(df)
        else:
            return self._format_create_table(db, df)
    
    def _format_create_table(self, db: NeuralDB, df: pd.DataFrame) -> str:
        """Format as SQL CREATE TABLE with sample rows."""
        result = db.get_create_table_sql() + "\n\n"
        result += "Sample rows:\n"
        
        # Format sample rows
        for idx, row in df.head(5).iterrows():
            values = ", ".join([f"'{str(v)}'" if isinstance(v, str) else str(v) for v in row])
            result += f"  ({values})\n"
        
        if len(df) > 5:
            result += f"  ... ({len(df)} total rows)\n"
        
        return result
    
    def _format_transpose(self, df: pd.DataFrame) -> str:
        """Format as transposed table (columns as rows)."""
        result = "Table (transposed):\n"
        
        for col in df.columns:
            values = df[col].head(5).tolist()
            value_str = ", ".join([str(v) for v in values])
            result += f"  {col}: {value_str}"
            if len(df) > 5:
                result += f", ... ({len(df)} values)"
            result += "\n"
        
        return result
    
    def _format_text(self, df: pd.DataFrame) -> str:
        """Format as pipe-separated text table."""
        result = "Table:\n"
        
        # Header
        result += " | ".join(df.columns) + "\n"
        result += "-" * (len(" | ".join(df.columns))) + "\n"
        
        # Rows
        for idx, row in df.iterrows():
            result += " | ".join([str(v) for v in row]) + "\n"
        
        return result
    
    def build_prompt_with_examples(
        self,
        template: str,
        examples: List[Dict[str, Any]],
        current_table: str,
        current_question: str
    ) -> str:
        """
        Build few-shot prompt with examples.
        
        Args:
            template: Base prompt template
            examples: List of example dictionaries with 'table', 'question', 'output'
            current_table: Formatted current table
            current_question: Current question to answer
            
        Returns:
            Complete prompt with examples and current query
        """
        prompt = template + "\n\n"
        
        # Add few-shot examples
        for i, example in enumerate(examples):
            prompt += f"Example {i + 1}:\n"
            prompt += f"Table:\n{example['table']}\n\n"
            prompt += f"Question: {example['question']}\n"
            prompt += f"Output: {example['output']}\n\n"
        
        # Add current query
        prompt += "Now solve this:\n"
        prompt += f"Table:\n{current_table}\n\n"
        prompt += f"Question: {current_question}\n"
        prompt += "Output:"
        
        return prompt
    
    def build_simple_prompt(
        self,
        instruction: str,
        table: str,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Build simple prompt without examples.
        
        Args:
            instruction: Task instruction
            table: Formatted table string
            question: Question to answer
            context: Optional additional context
            
        Returns:
            Complete prompt
        """
        prompt = instruction + "\n\n"
        
        if context:
            prompt += f"Context:\n{context}\n\n"
        
        prompt += f"Table:\n{table}\n\n"
        prompt += f"Question: {question}\n\n"
        prompt += "Output:"
        
        return prompt
