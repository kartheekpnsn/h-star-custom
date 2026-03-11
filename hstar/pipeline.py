"""Main H-STAR pipeline orchestrator."""

import os
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path

from hstar.config import Config
from hstar.generation.generator import Generator
from hstar.nsql.database import NeuralDB
from hstar.stages import (
    ColSQLStage,
    ColTextStage,
    RowSQLStage,
    RowTextStage,
    ReasonSQLStage,
    ReasonTextStage
)
from hstar.utils import save_stage_results


class HStar:
    """
    Main H-STAR pipeline orchestrator.
    
    Executes the full 6-stage pipeline:
    1. COL_SQL: Select relevant columns (SQL)
    2. COL_TEXT: Refine column selection (Text)
    3. ROW_SQL: Select relevant rows (SQL)
    4. ROW_TEXT: Refine row selection (Text)
    5. REASON_SQL: Generate final answer (SQL)
    6. REASON_TEXT: Generate final answer (Text)
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize H-STAR pipeline.
        
        Args:
            config: Configuration object (default: from environment)
        """
        self.config = config or Config.from_env()
        self.generator = Generator(self.config)
        
        # Initialize stages
        self.stages = [
            ColSQLStage(self.config, self.generator),
            ColTextStage(self.config, self.generator),
            RowSQLStage(self.config, self.generator),
            RowTextStage(self.config, self.generator),
            ReasonSQLStage(self.config, self.generator),
            ReasonTextStage(self.config, self.generator)
        ]
        
        # Create results directory if needed
        if self.config.save_intermediate:
            Path(self.config.results_dir).mkdir(parents=True, exist_ok=True)
    
    def run(
        self,
        table: pd.DataFrame,
        question: str,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run the full H-STAR pipeline.
        
        Args:
            table: Input table as pandas DataFrame
            question: Question to answer about the table
            save_results: Whether to save intermediate results
            
        Returns:
            Dictionary with final answer and all intermediate results
        """
        print("\n" + "="*60)
        print("H-STAR PIPELINE EXECUTION")
        print("="*60)
        print(f"Question: {question}")
        print(f"Table shape: {table.shape}")
        print("="*60 + "\n")
        
        # Initialize database
        db = NeuralDB(
            table=table,
            db_path=self.config.db_path,
            table_name=self.config.table_name
        )
        
        # Execute stages sequentially
        all_results = {
            "question": question,
            "table_shape": table.shape,
            "stages": {}
        }
        
        previous_results = None
        
        for stage in self.stages:
            stage_name = stage.get_stage_name()
            print(f"\n{'='*60}")
            print(f"Stage: {stage_name}")
            print(f"{'='*60}")
            
            try:
                # Run stage
                stage_results = stage.run(db, question, previous_results)
                
                # Store results
                all_results["stages"][stage_name] = stage_results
                previous_results = stage_results
                
                # Save intermediate results if enabled
                if save_results and self.config.save_intermediate:
                    output_path = os.path.join(
                        self.config.results_dir,
                        f"{stage_name.lower()}_results.json"
                    )
                    save_stage_results(stage_results, output_path)
                    print(f"Saved results to: {output_path}")
                
            except Exception as e:
                print(f"ERROR in stage {stage_name}: {e}")
                all_results["stages"][stage_name] = {
                    "error": str(e),
                    "stage": stage_name
                }
                # Continue to next stage with error noted
                continue
        
        # Extract final answer
        final_stage = all_results["stages"].get("REASON_TEXT", {})
        all_results["final_answer"] = final_stage.get("final_answer", "No answer generated")
        
        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"Final Answer: {all_results['final_answer']}")
        print("="*60 + "\n")
        
        # Save complete results
        if save_results:
            output_path = os.path.join(
                self.config.results_dir,
                "complete_results.json"
            )
            save_stage_results(all_results, output_path)
            print(f"Complete results saved to: {output_path}")
        
        return all_results
    
    def run_from_csv(
        self,
        csv_path: str,
        question: str,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run pipeline on a CSV file.
        
        Args:
            csv_path: Path to CSV file
            question: Question to answer
            save_results: Whether to save results
            
        Returns:
            Dictionary with final answer and all intermediate results
        """
        # Load CSV
        print(f"Loading CSV from: {csv_path}")
        table = pd.read_csv(csv_path)
        print(f"Loaded table with shape: {table.shape}")
        
        # Run pipeline
        return self.run(table, question, save_results)
