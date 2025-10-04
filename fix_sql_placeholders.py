#!/usr/bin/env python3
"""
Fix all SQL placeholders from SQLite (?) to PostgreSQL (%s)
Adds format_query() wrapper to all SQL queries with ? placeholders
"""
import os
import re
import sys

def add_format_query_import(content):
    """Add format_query import if not already present"""
    if 'from database_utils import format_query' in content:
        return content

    # Find where to add import
    import_section_end = 0
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_section_end = i

    # Insert after last import
    if import_section_end > 0:
        lines.insert(import_section_end + 1, 'from database_utils import format_query')
        return '\n'.join(lines)

    # If no imports, add at top after docstring
    for i, line in enumerate(lines):
        if '"""' in line or "'''" in line:
            # Find closing docstring
            for j in range(i+1, len(lines)):
                if '"""' in lines[j] or "'''" in lines[j]:
                    lines.insert(j+1, 'from database_utils import format_query')
                    return '\n'.join(lines)

    # Fallback: add at very top
    lines.insert(0, 'from database_utils import format_query')
    return '\n'.join(lines)

def wrap_queries_with_format(content):
    """Wrap SQL queries containing ? with format_query()"""
    # Pattern: cursor.execute("...?...", ...)
    # or cursor.execute("""...?...""", ...)

    # Single line queries with ?
    pattern1 = r'(cursor\.execute\s*\(\s*)(")([^"]*\?[^"]*")(\s*,)'
    content = re.sub(pattern1, r'\1format_query(\3)\4', content)

    pattern2 = r"(cursor\.execute\s*\(\s*)(')([^']*\?[^']*)(')"
    content = re.sub(pattern2, r'\1format_query(\3)\4', content)

    # Multi-line queries with ? (triple quotes)
    pattern3 = r'(cursor\.execute\s*\(\s*)(""")(.*?)(\s*"""\s*,)'
    def replace_multiline(match):
        if '?' in match.group(3):
            return f'{match.group(1)}format_query({match.group(2)}{match.group(3)}{match.group(4)[:-1]}){match.group(4)[-1]}'
        return match.group(0)

    content = re.sub(pattern3, replace_multiline, content, flags=re.DOTALL)

    return content

def fix_file(filepath):
    """Fix a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if no SQL queries with ?
        if '?' not in content or 'cursor.execute' not in content:
            return False

        # Add import
        content = add_format_query_import(content)

        # Wrap queries
        content = wrap_queries_with_format(content)

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    backend_dir = 'backend'
    fixed_count = 0

    for root, dirs, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    print(f"Fixed: {filepath}")
                    fixed_count += 1

    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()
