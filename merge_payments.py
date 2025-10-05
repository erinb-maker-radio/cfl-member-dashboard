#!/usr/bin/env python3
"""
Payment History Merger
Merges new Zeffy exports with historical master database
"""
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# Auto-detect environment
if os.name == 'nt':  # Windows
    MASTER_DB = r'C:\Users\erin\CFL Member Dashboard\payment_history_master.xlsx'
    EXPORT_FOLDER = r'C:\Users\erin\Zeffy_Exports'
else:  # Linux/Server
    MASTER_DB = '/var/www/cfl-member-dashboard/exports/payment_history_master.xlsx'
    EXPORT_FOLDER = '/var/www/cfl-member-dashboard/exports'

def get_latest_export():
    """Find the most recent Zeffy export file"""
    export_path = Path(EXPORT_FOLDER)
    files = list(export_path.glob('zeffy-payments-*.csv')) + list(export_path.glob('zeffy-payments-*.xlsx'))

    if not files:
        raise FileNotFoundError(f"No export files found in {EXPORT_FOLDER}")

    # Sort by modification time, get most recent
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file

def merge_payments():
    """Merge latest export with master database"""

    master_path = Path(MASTER_DB)

    # Load master database (or create if doesn't exist)
    if master_path.exists():
        print(f"Loading master database: {master_path}")
        df_master = pd.read_excel(master_path)
        print(f"  Master has {len(df_master)} records")
    else:
        print("⚠ No master database found, latest export will become master")
        df_master = pd.DataFrame()

    # Load latest export
    latest_file = get_latest_export()
    print(f"Loading latest export: {latest_file}")

    if latest_file.suffix == '.csv':
        df_new = pd.read_excel(latest_file)  # Zeffy "CSV" is actually Excel
    else:
        df_new = pd.read_excel(latest_file)

    print(f"  Latest export has {len(df_new)} records")

    # If no master, use latest as master
    if df_master.empty:
        df_merged = df_new.copy()
        print(f"✓ Created new master database with {len(df_merged)} records")
    else:
        # Merge: add new records, update existing ones
        # Use Email + Payment Date as unique key

        # Ensure consistent columns
        if set(df_master.columns) != set(df_new.columns):
            print("⚠ Column mismatch, aligning columns...")
            # Use columns from new export (most recent structure)
            missing_in_master = set(df_new.columns) - set(df_master.columns)
            for col in missing_in_master:
                df_master[col] = None

        # Concatenate and remove duplicates
        df_merged = pd.concat([df_master, df_new], ignore_index=True)

        # Remove exact duplicates based on Email + Payment Date
        date_col = 'Payment Date (UTC)' if 'Payment Date (UTC)' in df_merged.columns else 'Payment Date (America/Los_Angeles)'

        initial_count = len(df_merged)
        df_merged = df_merged.drop_duplicates(subset=['Email', date_col], keep='last')
        duplicates_removed = initial_count - len(df_merged)

        print(f"✓ Merged data: {len(df_merged)} total records ({duplicates_removed} duplicates removed)")

    # Save updated master
    master_path.parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_excel(master_path, index=False)
    print(f"✓ Saved master database: {master_path}")

    # Create backup with timestamp
    backup_path = master_path.parent / f"payment_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df_merged.to_excel(backup_path, index=False)
    print(f"✓ Backup saved: {backup_path}")

    return master_path

if __name__ == "__main__":
    try:
        master_file = merge_payments()
        print(f"\n✓ Master database ready: {master_file}")
        print("Run analyze_members.py to generate dashboard from master database")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
