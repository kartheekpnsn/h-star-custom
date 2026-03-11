# CSV to SQLite Conversion Scripts

This folder contains utilities for converting CSV files to SQLite databases with validation.

## Scripts

### 1. `csv_to_sqlite.py` - Main Conversion Script

Converts CSV files to SQLite databases and validates the conversion.

**Usage:**
```bash
# Basic usage - creates db/<csv_name>.db
uv run python scripts/csv_to_sqlite.py data/titanic.csv

# Specify output database name
uv run python scripts/csv_to_sqlite.py data/titanic.csv my_custom.db

# Custom table name
uv run python scripts/csv_to_sqlite.py data/titanic.csv --table passengers

# Skip validation (faster)
uv run python scripts/csv_to_sqlite.py data/titanic.csv --skip-validation
```

**Features:**
- ✅ Automatic database file creation in `db/` folder
- ✅ Comprehensive validation (row count, columns, data integrity)
- ✅ Data hash verification to ensure perfect match
- ✅ Detailed progress and statistics reporting

**Output Example:**
```
================================================================================
CSV to SQLite Converter
================================================================================
📁 Loading CSV: data/titanic.csv
   └─ Rows: 891, Columns: 12
   └─ Columns: PassengerId, Survived, Pclass, Name, Sex, Age...
   └─ Data hash: 9a4bcd798a058b35...

💾 Creating SQLite database: db/titanic.db
   ✓ Table 'dataset' created
   └─ Columns: 12
   └─ Rows: 891

🔍 Validating database: db/titanic.db
   ✓ Table 'dataset' exists
   ✓ Row count matches
   ✓ Column count matches
   ✓ Column names match
   ✓ All data types match
   ✓ Data hash matches perfectly
   
✅ Validation PASSED! Database is correct.
```

### 2. `verify_db.py` - Database Verification Script

Inspects and displays database contents.

**Usage:**
```bash
uv run python scripts/verify_db.py db/titanic.db
```

**Features:**
- 📊 Lists all tables
- 📋 Shows schema for each table
- 📄 Displays sample rows
- 📊 Column statistics (unique values, null counts)
- 💾 File size information

## Examples

### Convert Titanic Dataset
```bash
# Convert the Titanic CSV
uv run python scripts/csv_to_sqlite.py data/titanic.csv

# Result: db/titanic.db created with 891 rows, 12 columns

# Verify the database
uv run python scripts/verify_db.py db/titanic.db
```

### Query the Database Directly

Using Python:
```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('db/titanic.db')

# Run queries
df = pd.read_sql('SELECT * FROM dataset WHERE Age > 60', conn)
print(df)

# Get statistics
stats = pd.read_sql('''
    SELECT 
        Pclass,
        COUNT(*) as passengers,
        AVG(Age) as avg_age,
        SUM(CASE WHEN Survived = 1 THEN 1 ELSE 0 END) as survivors
    FROM dataset
    GROUP BY Pclass
''', conn)
print(stats)

conn.close()
```

Using sqlite3 CLI:
```bash
sqlite3 db/titanic.db

# Once in sqlite3 prompt:
.tables                    # List tables
.schema dataset           # Show schema
SELECT COUNT(*) FROM dataset;
SELECT * FROM dataset LIMIT 5;
.quit
```

## Validation Process

The script validates:

1. **Row Count** - Ensures all rows were imported
2. **Column Count** - Verifies structure is preserved
3. **Column Names** - Checks all columns exist with correct names
4. **Data Types** - Reports any type conversions
5. **Data Hash** - MD5 hash verification for data integrity
6. **Cell-by-cell Comparison** - If hash differs, checks individual values

## Database Structure

All databases are stored in the `db/` folder with this structure:

```
db/
├── titanic.db       # From data/titanic.csv
├── feta_qa.db       # From data/fetaQA-v1_train.csv (if converted)
└── sample.db        # From data/sample_table.csv (if converted)
```

Default table name: `dataset` (can be customized with `--table` flag)

## Troubleshooting

**Database file already exists:**
- The script automatically removes existing files with the same name

**Validation fails:**
- Check CSV file encoding (should be UTF-8)
- Verify CSV is not corrupted
- Look at the detailed error message to identify the issue

**Large CSV files:**
- Use `--skip-validation` for very large files (>1GB)
- The conversion will still work, just won't verify

## Requirements

All dependencies are managed by `uv` and include:
- pandas
- sqlite3 (built-in)
- pathlib (built-in)
