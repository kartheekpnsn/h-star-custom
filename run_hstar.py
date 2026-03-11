#!/usr/bin/env python3
"""Command-line interface for H-STAR pipeline."""

import argparse
import sys
from pathlib import Path

from hstar import HStar, Config


def main():
    """Main CLI entry point."""

    MODEL_NAME = "gpt-5.4"  # Change to your desired model
    CSV_PATH = "data/sample_table.csv"
    DEFAULT_QUESTION = "What is the population of France?"
    CSV_PATH = "data/titanic.csv"
    DEFAULT_QUESTION = "Which gender survived more on the Titanic, and what was the average age of survivors?"
    DEFAULT_QUESTION = "Why did female passengers have a higher survival rate?"
    
    # Create configuration
    try:
        config = Config.from_env(model_name=MODEL_NAME)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nMake sure you have set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT")
        print("in your .env file or environment variables.")
        sys.exit(1)
    
    # Initialize and run pipeline
    try:
        hstar = HStar(config)
        results = hstar.run_from_csv(
            csv_path=CSV_PATH,
            question=DEFAULT_QUESTION,
            save_results=False  # Set to True to save final results
        )
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Question: {DEFAULT_QUESTION}")
        print(f"Answer: {results['final_answer']}")
        print("="*60)
        
        # Exit successfully
        sys.exit(0)
        
    except Exception as e:
        print(f"\nPipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
