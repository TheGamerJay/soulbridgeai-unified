#!/usr/bin/env python3
"""Final fix for ALL cursor.execute syntax errors"""

import os
import re
from pathlib import Path

def fix_all_execute(file_path):
    """Fix both format_query and non-format_query cursor.execute calls"""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Pattern 1: Non-format_query cases - execute("""..."""), (params)) -> execute("""...""", (params))
    # Only match when NOT preceded by format_query
    pattern1 = r'(?<!format_query\()cursor\.execute\("""[^"]*"""\),\s*\([^)]+\)\)'

    def replace1(match):
        # Remove the ) before the comma
        return match.group(0).replace('"""),', '""",')

    fixed = re.sub(pattern1, replace1, content, flags=re.DOTALL)

    if fixed != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed)
        return True
    return False

if __name__ == '__main__':
    backend_dir = Path(__file__).parent
    fixed_count = 0

    for py_file in backend_dir.rglob('*.py'):
        if fix_all_execute(py_file):
            print(f'Fixed: {py_file}')
            fixed_count += 1

    print(f'\nTotal files fixed: {fixed_count}')
