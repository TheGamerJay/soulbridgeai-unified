#!/usr/bin/env python3
"""
Cleanup Script - Remove Deprecated Endpoints
Run this after frontend is migrated to v1 API
"""

import re
import os
from pathlib import Path

def find_deprecated_endpoints():
    """Find all endpoints that should be removed"""
    deprecated_endpoints = [
        # Replaced by /v1/entitlements
        "/api/user-status",
        "/api/trial-status", 
        "/api/user-plan",
        "/api/tier-limits",
        "/api/user/tier-status",
        "/api/plan",
        "/api/get-current-plan",
        
        # Replaced by /v1/me
        "/api/user-info",
        
        # Replaced by /v1/credits or /v1/entitlements
        "/api/decoder/check-limit",
        "/api/fortune/check-limit",
        "/api/horoscope/check-limit",
    ]
    
    return deprecated_endpoints

def remove_endpoint_from_file(file_path, endpoint_pattern):
    """Remove an endpoint and its function from app.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match the entire endpoint function
    pattern = rf'@app\.route\("{re.escape(endpoint_pattern)}"[^@]*?(?=@app\.route|def \w+|$)'
    
    # Find and remove the endpoint
    matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
    for match in matches:
        print(f"  Found endpoint: {endpoint_pattern}")
        # Remove the matched content
        content = content.replace(match.group(0), "")
    
    return content

def cleanup_app_py():
    """Remove deprecated endpoints from app.py"""
    app_py_path = Path(__file__).parent / "app.py"
    
    if not app_py_path.exists():
        print("❌ app.py not found")
        return False
    
    print("🧹 Starting cleanup of deprecated endpoints...")
    
    # Read original file
    with open(app_py_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Backup original file
    backup_path = app_py_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print(f"📦 Backup created: {backup_path}")
    
    # Clean up each deprecated endpoint
    content = original_content
    deprecated_endpoints = find_deprecated_endpoints()
    
    for endpoint in deprecated_endpoints:
        print(f"🗑️  Removing {endpoint}...")
        content = remove_endpoint_from_file_content(content, endpoint)
    
    # Write cleaned content
    with open(app_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Calculate savings
    original_lines = len(original_content.splitlines())
    new_lines = len(content.splitlines())
    removed_lines = original_lines - new_lines
    
    print(f"✅ Cleanup complete!")
    print(f"📊 Removed {removed_lines} lines of code")
    print(f"📊 Cleaned {len(deprecated_endpoints)} deprecated endpoints")
    
    return True

def remove_endpoint_from_file_content(content, endpoint_path):
    """Remove endpoint function from content string"""
    lines = content.splitlines()
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts an endpoint we want to remove
        if f'@app.route("{endpoint_path}"' in line:
            print(f"  Removing endpoint: {endpoint_path}")
            
            # Skip the @app.route line
            i += 1
            
            # Skip any additional decorators
            while i < len(lines) and lines[i].strip().startswith('@'):
                i += 1
            
            # Skip the function definition and body
            if i < len(lines) and lines[i].strip().startswith('def '):
                # Found function definition
                func_indent = len(lines[i]) - len(lines[i].lstrip())
                i += 1  # Skip def line
                
                # Skip function body (all lines indented more than function)
                while i < len(lines):
                    if lines[i].strip() == "":
                        # Empty line - keep going
                        i += 1
                        continue
                    
                    line_indent = len(lines[i]) - len(lines[i].lstrip())
                    if line_indent <= func_indent and lines[i].strip():
                        # We've reached the end of the function
                        break
                    
                    i += 1
                
                # Don't increment i here - we want to process the current line
                continue
        else:
            new_lines.append(line)
            i += 1
    
    return '\n'.join(new_lines)

def main():
    """Main cleanup function"""
    print("🚮 SoulBridge AI - Deprecated Endpoint Cleanup")
    print("=" * 50)
    
    # Check if v1 API is implemented
    v1_api_path = Path(__file__).parent / "v1_api.py"
    if not v1_api_path.exists():
        print("❌ v1_api.py not found - implement v1 API first!")
        return False
    
    # Ask for confirmation
    response = input("⚠️  This will remove deprecated endpoints. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cleanup cancelled")
        return False
    
    # Perform cleanup
    success = cleanup_app_py()
    
    if success:
        print("\n🎉 Cleanup completed successfully!")
        print("📝 Next steps:")
        print("   1. Test the application thoroughly")
        print("   2. Update frontend to use v1 API endpoints")
        print("   3. Remove any remaining references to old endpoints")
    
    return success

if __name__ == "__main__":
    main()