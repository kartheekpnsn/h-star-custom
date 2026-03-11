#!/usr/bin/env python3
"""
Convert CSV files to SQLite databases with validation.

Usage:
    python scripts/csv_to_sqlite.py <csv_file> [output_db_name]
    
Example:
    python scripts/csv_to_sqlite.py data/titanic.csv titanic.db
"""

import sqlite3
import pandas as pd
import argparse
from pathlib import Path
import sys
import hashlib


def get_dataframe_hash(df: pd.DataFrame) -> str:
    """Generate hash of dataframe for comparison."""
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()


def csv_to_sqlite(csv_path: Path, db_path: Path, table_name: str = "dataset") -> dict:
    """
    Convert CSV file to SQLite database.
    
    Args:
        csv_path: Path to input CSV file
        db_path: Path to output SQLite database
        table_name: Name for the table in database
        
    Returns:
        Dictionary with conversion statistics
    """
    print(f"📁 Loading CSV: {csv_path}")
    
    # Load CSV
    df = pd.read_csv(csv_path)
    original_hash = get_dataframe_hash(df)
    
    print(f"   └─ Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"   └─ Columns: {', '.join(df.columns.tolist())}")
    print(f"   └─ Data hash: {original_hash[:16]}...")
    
    # Create db directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if present
    if db_path.exists():
        print(f"⚠️  Removing existing database: {db_path}")
        db_path.unlink()
    
    # Create SQLite database
    print(f"\n💾 Creating SQLite database: {db_path}")
    conn = sqlite3.connect(str(db_path))
    
    # Write DataFrame to SQLite
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    
    # Get table info
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"   ✓ Table '{table_name}' created")
    print(f"   └─ Columns: {len(columns)}")
    print(f"   └─ Rows: {row_count}")
    
    return {
        "csv_path": csv_path,
        "db_path": db_path,
        "table_name": table_name,
        "original_df": df,
        "original_hash": original_hash,
        "row_count": row_count,
        "column_count": len(columns)
    }


def validate_database(db_path: Path, table_name: str, original_df: pd.DataFrame, original_hash: str) -> bool:
    """
    Validate that SQLite database matches original CSV.
    
    Args:
        db_path: Path to SQLite database
        table_name: Name of table to validate
        original_df: Original DataFrame from CSV
        original_hash: Hash of original DataFrame
        
    Returns:
        True if validation passes, False otherwise
    """
    print(f"\n🔍 Validating database: {db_path}")
    
    if not db_path.exists():
        print(f"   ✗ Database file not found!")
        return False
    
    # Load data from SQLite
    conn = sqlite3.connect(str(db_path))
    
    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        print(f"   ✗ Table '{table_name}' not found!")
        conn.close()
        return False
    
    print(f"   ✓ Table '{table_name}' exists")
    
    # Load DataFrame from SQLite
    loaded_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    loaded_hash = get_dataframe_hash(loaded_df)
    
    conn.close()
    
    # Validate row count
    print(f"\n   Row Count:")
    print(f"      Original: {len(original_df)}")
    print(f"      Loaded:   {len(loaded_df)}")
    
    if len(original_df) != len(loaded_df):
        print(f"   ✗ Row count mismatch!")
        return False
    print(f"   ✓ Row count matches")
    
    # Validate column count
    print(f"\n   Column Count:")
    print(f"      Original: {len(original_df.columns)}")
    print(f"      Loaded:   {len(loaded_df.columns)}")
    
    if len(original_df.columns) != len(loaded_df.columns):
        print(f"   ✗ Column count mismatch!")
        return False
    print(f"   ✓ Column count matches")
    
    # Validate column names
    print(f"\n   Column Names:")
    original_cols = set(original_df.columns)
    loaded_cols = set(loaded_df.columns)
    
    if original_cols != loaded_cols:
        missing = original_cols - loaded_cols
        extra = loaded_cols - original_cols
        if missing:
            print(f"   ✗ Missing columns: {missing}")
        if extra:
            print(f"   ✗ Extra columns: {extra}")
        return False
    print(f"   ✓ Column names match")
    
    # Validate data types
    print(f"\n   Data Types:")
    type_mismatches = []
    for col in original_df.columns:
        orig_type = original_df[col].dtype
        load_type = loaded_df[col].dtype
        if orig_type != load_type:
            type_mismatches.append((col, orig_type, load_type))
    
    if type_mismatches:
        print(f"   ⚠️  Data type differences (expected for SQLite):")
        for col, orig, load in type_mismatches:
            print(f"      {col}: {orig} -> {load}")
    else:
        print(f"   ✓ All data types match")
    
    # Validate data hash
    print(f"\n   Data Hash:")
    print(f"      Original: {original_hash[:16]}...")
    print(f"      Loaded:   {loaded_hash[:16]}...")
    
    if original_hash == loaded_hash:
        print(f"   ✓ Data hash matches perfectly")
    else:
        print(f"   ⚠️  Data hash differs (checking cell-by-cell...)")
        
        # Compare values cell by cell
        differences = []
        for col in original_df.columns:
            # Sort both for comparison
            orig_sorted = original_df[col].sort_values().reset_index(drop=True)
            load_sorted = loaded_df[col].sort_values().reset_index(drop=True)
            
            # Compare handling NaN
            mask = (orig_sorted != load_sorted) & ~(orig_sorted.isna() & load_sorted.isna())
            if mask.any():
                diff_count = mask.sum()
                differences.append((col, diff_count))
        
        if differences:
            print(f"   ✗ Data differences found:")
            for col, count in differences:
                print(f"      {col}: {count} differing values")
            return False
        else:
            print(f"   ✓ All cell values match (hash difference likely due to precision)")
    
    # Database file size
    file_size = db_path.stat().st_size
    print(f"\n   Database Size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    
    print(f"\n✅ Validation PASSED! Database is correct.")
    return True


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(
        description="Convert CSV files to SQLite databases with validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/titanic.csv
  %(prog)s data/titanic.csv titanic.db
  %(prog)s data/fetaQA-v1_train.csv feta_qa.db
        """
    )
    
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to input CSV file"
    )
    
    parser.add_argument(
        "output_db",
        type=str,
        nargs="?",
        help="Output database name (default: <csv_name>.db)"
    )
    
    parser.add_argument(
        "--table",
        type=str,
        default="dataset",
        help="Table name in database (default: dataset)"
    )
    
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation step"
    )
    
    args = parser.parse_args()
    
    # Validate input
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Determine output path
    if args.output_db:
        db_path = Path("db") / args.output_db
    else:
        db_path = Path("db") / f"{csv_path.stem}.db"
    
    print("=" * 80)
    print("CSV to SQLite Converter")
    print("=" * 80)
    
    # Convert CSV to SQLite
    result = csv_to_sqlite(csv_path, db_path, args.table)
    
    # Validate if not skipped
    if not args.skip_validation:
        success = validate_database(
            db_path,
            args.table,
            result["original_df"],
            result["original_hash"]
        )
        
        if not success:
            print("\n❌ Validation FAILED!")
            sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ Conversion completed successfully!")
    print("=" * 80)
    print(f"Database: {db_path}")
    print(f"Table: {args.table}")
    print(f"Rows: {result['row_count']}")
    print(f"Columns: {result['column_count']}")


if __name__ == "__main__":
    main()
