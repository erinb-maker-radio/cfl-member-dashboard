#!/usr/bin/env python3
"""
CGI endpoint to trigger dashboard data refresh
"""
import subprocess
import json
import sys
import os

# Change to the dashboard directory
os.chdir('/var/www/cfl-member-dashboard')

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

try:
    # Run zeffy export with venv python
    venv_python = '/var/www/cfl-member-dashboard/venv/bin/python3'
    result1 = subprocess.run([venv_python, 'zeffy_export.py'],
                            capture_output=True,
                            text=True,
                            timeout=120)

    if result1.returncode != 0:
        print(json.dumps({
            'success': False,
            'error': 'Zeffy export failed',
            'details': result1.stderr
        }))
        sys.exit(1)

    # Run analysis
    result2 = subprocess.run([venv_python, 'analyze_members.py'],
                            capture_output=True,
                            text=True,
                            timeout=60)

    if result2.returncode != 0:
        print(json.dumps({
            'success': False,
            'error': 'Analysis failed',
            'details': result2.stderr
        }))
        sys.exit(1)

    print(json.dumps({
        'success': True,
        'message': 'Dashboard data refreshed successfully'
    }))

except subprocess.TimeoutExpired:
    print(json.dumps({
        'success': False,
        'error': 'Update timed out'
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e)
    }))
