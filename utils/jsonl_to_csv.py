"""
Convert JSONL file to CSV format.

This script reads a JSONL (JSON Lines) file and converts it to CSV format.
Nested structures (lists, dicts) are converted to JSON strings in the CSV.
"""

import json
import csv
import sys
from pathlib import Path


def jsonl_to_csv(input_file: str, output_file: str = None) -> None:
    """
    Convert a JSONL file to CSV format.
    
    Args:
        input_file: Path to the input JSONL file
        output_file: Path to the output CSV file. If None, uses same name as input with .csv extension
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Generate output filename if not provided
    if output_file is None:
        output_file = input_path.with_suffix('.csv')
    else:
        output_file = Path(output_file)
    
    # Read all lines to determine all possible keys
    all_keys = set()
    data_lines = []
    
    print(f"Reading {input_file}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                all_keys.update(data.keys())
                data_lines.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping line {line_num} due to JSON decode error: {e}")
                continue
    
    if not data_lines:
        raise ValueError("No valid JSON data found in input file")
    
    # Sort keys for consistent column order
    fieldnames = sorted(all_keys)
    
    print(f"Writing {len(data_lines)} records to {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for data in data_lines:
            # Convert nested structures to JSON strings
            row = {}
            for key in fieldnames:
                value = data.get(key, '')
                
                # Convert lists and dicts to JSON strings
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            
            writer.writerow(row)
    
    print(f"✓ Successfully converted {input_file} to {output_file}")
    print(f"  Records: {len(data_lines)}")
    print(f"  Columns: {len(fieldnames)}")


def main():
    """Main entry point for the script."""
    
    input_file = "data/fetaQA-v1_train.jsonl"  # Default input file
    output_file = "data/fetaQA-v1_train.csv"  # Default output file
    
    try:
        jsonl_to_csv(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
