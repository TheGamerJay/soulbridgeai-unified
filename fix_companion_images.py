#!/usr/bin/env python3
"""Fix all companion image references to use skin naming system"""
import os
import re

replacements = {
    'GamerJay_premium_companion.png': 'GamerJay skin.png',
    'GamerJay_Premium_companion.png': 'GamerJay skin.png',
    'Blayzo_premium_companion.png': 'Blayzo skin.png',
    'WatchDog_a_Premium_companion.png': 'Watch Dog skin.png',
    'WatchDog_a_Max_Companion.png': 'Watch Dog skin.png',
    'Crimson_a_Max_companion.png': 'Crimson skin.png',
    'Dr. MadJay.png': 'Dr.MadJay skin.png',
}

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        changed = False
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                changed = True

        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"Error: {filepath} - {e}")
        return False

def main():
    fixed = 0
    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                if fix_file(os.path.join(root, file)):
                    fixed += 1

    print(f"\nFixed {fixed} files")

if __name__ == '__main__':
    main()
