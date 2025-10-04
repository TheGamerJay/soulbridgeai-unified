#!/usr/bin/env python3
"""
Fix cursor.execute() syntax errors where there's an extra closing parenthesis
Changes pattern from: cursor.execute triple-quote-close-paren-comma to triple-quote-comma
"""

import os
import re

def fix_cursor_execute(file_path):
    """Fix cursor.execute syntax in a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: cursor.execute("""...""", (params))
    # Should be: cursor.execute("""...""", (params))
    pattern = r'(cursor\.execute\([^)]+"""\)),\s*(\([^)]+\)\))'

    def replacer(match):
        # Remove the extra ) before the comma
        return match.group(1)[:-1] + ', ' + match.group(2)

    fixed_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

    if fixed_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        return True
    return False

if __name__ == '__main__':
    import sys
    from pathlib import Path

    backend_dir = Path(__file__).parent
    fixed_count = 0

    for py_file in backend_dir.rglob('*.py'):
        if fix_cursor_execute(py_file):
            print(f'Fixed: {py_file}')
            fixed_count += 1

    print(f'\nTotal files fixed: {fixed_count}')
