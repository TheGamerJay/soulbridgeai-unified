#!/usr/bin/env python3
"""
Final comprehensive fix for all format_query() syntax errors.
Fixes multiline format_query calls with incorrect parenthesis placement.
"""

import re
from pathlib import Path

def fix_format_query_multiline(file_path):
    """Fix format_query calls that span multiple lines"""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Pattern: format_query(""" ... """, (...))
    # Should be: format_query(""" ... """), (...))
    # This handles multiline queries with complex params

    # Match format_query with triple-quoted string and params tuple
    # Use recursive pattern to match nested parentheses
    pattern = r'(format_query\((?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'))\s*,\s*(\([^)]*(?:\([^)]*\))*[^)]*\))\)'

    def replacer(match):
        query_part = match.group(1)  # format_query("""..."""
        params = match.group(2)  # The (params) tuple
        return f'{query_part}), {params})'

    fixed = re.sub(pattern, replacer, content)

    if fixed != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed)
        return True
    return False

if __name__ == '__main__':
    backend_dir = Path(__file__).parent
    fixed_count = 0

    # Fix all Python files in modules directory
    for py_file in backend_dir.glob('modules/**/*.py'):
        try:
            if fix_format_query_multiline(py_file):
                print(f'Fixed: {py_file}')
                fixed_count += 1
        except Exception as e:
            print(f'Error fixing {py_file}: {e}')

    print(f'\nTotal files fixed: {fixed_count}')
