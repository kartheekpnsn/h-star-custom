#!/usr/bin/env python3
"""Command-line interface for H-STAR pipeline."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from hstar import HStar, Config


def main():
    """Main CLI entry point."""

    MODEL_NAME = os.environ.get("HSTAR_MODEL_NAME", "gpt-5.1")
    DB_PATH = os.environ.get("HSTAR_DB_PATH", "db/drug_shipments_200.db")
    DEFAULT_QUESTION = "What are the top 5 drugs by total shipment quantity?"
    
    # Create configuration
    try:
        config = Config.from_env(model_name=MODEL_NAME)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nMake sure you have set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT")
        print("in your .env file or environment variables.")
        sys.exit(1)
    
    # Initialize pipeline and load data once
    try:
        hstar = HStar(config)
        hstar.load_data(db_path=DB_PATH)

        results = hstar.run(
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
