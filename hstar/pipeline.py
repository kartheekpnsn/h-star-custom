"""Main H-STAR pipeline orchestrator."""

import os
import sqlite3
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
        self._source_table: Optional[pd.DataFrame] = None
        
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
    
    def load_data(
        self,
        csv_path: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> None:
        """
        Load table data once from an existing SQLite DB or CSV file.

        The loaded DataFrame is cached internally so that subsequent
        ``run()`` calls can create lightweight in-memory copies without
        re-reading the source.

        Args:
            csv_path: Path to a CSV file.
            db_path:  Path to an existing SQLite database file.
                      Takes precedence over *csv_path* when both are given.
        """
        if db_path:
            conn = sqlite3.connect(db_path)
            self._source_table = pd.read_sql_query(
                f"SELECT * FROM {self.config.table_name}", conn
            )
            conn.close()
            print(f"Loaded table from DB: {db_path} (shape: {self._source_table.shape})")
        elif csv_path:
            self._source_table = pd.read_csv(csv_path)
            print(f"Loaded table from CSV: {csv_path} (shape: {self._source_table.shape})")
        else:
            raise ValueError("Either csv_path or db_path must be provided")

    def run(
        self,
        question: str,
        table: Optional[pd.DataFrame] = None,
        column_desc: Optional[str] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run the full H-STAR pipeline.
        
        Uses cached data from ``load_data()`` when *table* is not supplied.
        Each call creates a fresh in-memory NeuralDB copy so the source
        data is never mutated.

        Args:
            question: Question to answer about the table
            table: Input table as pandas DataFrame (optional if load_data was called)
            column_desc: Optional description of columns to assist reasoning
            save_results: Whether to save intermediate results
            
        Returns:
            Dictionary with final answer and all intermediate results
        """
        source = table if table is not None else self._source_table
        if source is None:
            raise ValueError(
                "No table data available. Call load_data() first or pass a table."
            )

        print("\n" + "="*60)
        print("H-STAR PIPELINE EXECUTION")
        print("="*60)
        print(f"Question: {question}")
        print(f"Table shape: {source.shape}")
        print("="*60 + "\n")
        
        # Create a fresh in-memory NeuralDB copy for this query
        db = NeuralDB(
            table=source.copy(),
            db_path=":memory:",
            table_name=self.config.table_name
        )
        
        # Execute stages sequentially
        all_results = {
            "question": question,
            "table_shape": source.shape,
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
                if stage_name not in ["COL_TEXT", "COL_SQL"]:
                    column_desc = None  # Clear column description for text refinement stages
                stage_results = stage.run(db, question, column_desc, previous_results)
                
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
        column_desc: Optional[str] = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run pipeline on a CSV file.

        Loads the data once (preferring an existing DB in ``db/``) and
        caches it for future calls.
        
        Args:
            csv_path: Path to CSV file
            question: Question to answer
            column_desc: Optional description of columns to assist reasoning
            save_results: Whether to save results
            
        Returns:
            Dictionary with final answer and all intermediate results
        """
        if self._source_table is None:
            # Prefer existing DB file over re-reading CSV
            db_file = str(Path("db") / f"{Path(csv_path).stem}.db")
            if os.path.exists(db_file):
                self.load_data(db_path=db_file)
            else:
                self.load_data(csv_path=csv_path)
        
        return self.run(question=question, column_desc=column_desc, save_results=save_results)
