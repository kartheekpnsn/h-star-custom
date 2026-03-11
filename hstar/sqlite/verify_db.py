#!/usr/bin/env python3
"""Quick script to verify SQLite database contents."""

import sqlite3
import pandas as pd
import sys
from pathlib import Path


def verify_database(db_path: str):
    """Verify and display database contents."""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    print(f"🔍 Verifying database: {db_path}")
    print("=" * 80)
    
    # Connect to the database
    conn = sqlite3.connect(str(db_file))
    
    # Show tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'\n📊 Tables: {[t[0] for t in tables]}')
    
    for table_name in [t[0] for t in tables]:
        print(f"\n{'='*80}")
        print(f"📋 Table: {table_name}")
        print(f"{'='*80}")
        
        # Show schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f'\nSchema ({len(columns)} columns):')
        for col in columns:
            print(f'   {col[1]:20s} {col[2]}')
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Sample query
        df = pd.read_sql(f'SELECT * FROM {table_name} LIMIT 5', conn)
        print(f'\n📄 Sample rows (showing 5 of {row_count} total):')
        print(df.to_string(index=False))
        
        # Column statistics
        print('\n📊 Column Statistics:')
        for col_info in columns:
            col_name = col_info[1]
            col_type = col_info[2]
            
            cursor.execute(f'SELECT COUNT(DISTINCT {col_name}) as unique_count FROM {table_name}')
            unique_count = cursor.fetchone()[0]
            
            cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL')
            null_count = cursor.fetchone()[0]
            
            print(f'   {col_name:20s} | Unique: {unique_count:4d} | Nulls: {null_count:4d}')
    
    conn.close()
    
    # File size
    file_size = db_file.stat().st_size
    print(f'\n💾 Database file size: {file_size:,} bytes ({file_size / 1024:.2f} KB)')
    
    print(f"\n{'='*80}")
    print("✅ Verification complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_db.py <database_path>")
        print("\nExample:")
        print("  python verify_db.py db/titanic.db")
        sys.exit(1)
    
    verify_database(sys.argv[1])
