#!/usr/bin/env python3
"""
Final fix for format_query cursor.execute syntax
Correct pattern: cursor.execute(format_query("SELECT..."), (params))
"""

import os
import re
from pathlib import Path

def fix_format_query_calls(file_path):
    """Fix all format_query cursor.execute calls"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: format_query("""..."""), (params)) -> format_query("""..."""), (params))
    # This regex matches across lines
    pattern1 = r'(cursor\.execute\(format_query\("""[^"]*""")(?:\s*),\s*(\([^)]+\))\)'

    def replace1(match):
        return match.group(1) + '), ' + match.group(2) + ')'

    fixed = re.sub(pattern1, replace1, content, flags=re.DOTALL)

    # Pattern 2: Multiline - split across lines
    pattern2 = r'(cursor\.execute\(format_query\((?:"""|\'\'\'|"|\')\s*\n[\s\S]*?(?:"""|\'\'\'|"|\')),\s*(\([^)]+\))\)'

    def replace2(match):
        return match.group(1) + '), ' + match.group(2) + ')'

    fixed = re.sub(pattern2, replace2, fixed, flags=re.DOTALL)

    if fixed != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed)
        return True
    return False

if __name__ == '__main__':
    backend_dir = Path(__file__).parent
    fixed_count = 0

    for py_file in backend_dir.rglob('*.py'):
        if fix_format_query_calls(py_file):
            print(f'Fixed: {py_file}')
            fixed_count += 1

    print(f'\nTotal files fixed: {fixed_count}')
