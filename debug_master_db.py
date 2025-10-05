#!/usr/bin/env python3
"""
Debug script to check master database usage
"""
import sys
import os
from pathlib import Path

os.chdir('/var/www/cfl-member-dashboard')
sys.path.insert(0, '/var/www/cfl-member-dashboard')

# Import the function
from analyze_members import get_latest_export_file

print("=" * 60)
print("MASTER DATABASE DEBUG")
print("=" * 60)

master_path = Path('/var/www/cfl-member-dashboard/exports/payment_history_master.xlsx')
print(f"\nMaster database path: {master_path}")
print(f"Master exists: {master_path.exists()}")

if master_path.exists():
    print(f"Master size: {master_path.stat().st_size} bytes")
    print(f"Master modified: {master_path.stat().st_mtime}")

print("\nCalling get_latest_export_file()...")
latest = get_latest_export_file()
print(f"Result: {latest}")

if latest == master_path:
    print("\n✓ SUCCESS: Using master database")
else:
    print(f"\n✗ ERROR: Not using master, using {latest} instead")
    print("\nChecking why...")

    # Check if master actually has data
    import pandas as pd
    try:
        df = pd.read_excel(master_path)
        print(f"Master has {len(df)} rows")
        print(f"Columns: {df.columns.tolist()[:5]}")

        # Check for Ryan
        ryan = df[df['Email'].str.contains('ryan', case=False, na=False)]
        if len(ryan) > 0:
            print(f"\nRyan found in master: {len(ryan)} payments")
            dates = ryan['Payment Date (UTC)' if 'Payment Date (UTC)' in df.columns else 'Payment Date (America/Los_Angeles)']
            print(f"Date range: {dates.min()} to {dates.max()}")
        else:
            print("\nRyan NOT found in master!")
    except Exception as e:
        print(f"Error reading master: {e}")
