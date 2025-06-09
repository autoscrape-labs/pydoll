#!/usr/bin/env python3
"""Fix NotRequired imports for Python 3.10 compatibility."""

import os
import re
from pathlib import Path

def fix_notrequired_import(file_path):
    """Fix NotRequired import in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match direct NotRequired import
        pattern1 = r'^from typing import NotRequired$'
        replacement1 = '''try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired'''
        
        # Pattern to match NotRequired with other imports
        pattern2 = r'^from typing import (.+, )?NotRequired(, .+)?$'
        
        def replace_multi_import(match):
            full_match = match.group(0)
            before = match.group(1) or ''
            after = match.group(2) or ''
            
            # Extract other imports
            other_imports = []
            if before:
                other_imports.extend([imp.strip() for imp in before.rstrip(', ').split(',')])
            if after:
                other_imports.extend([imp.strip() for imp in after.lstrip(', ').split(',')])
            
            # Remove empty strings
            other_imports = [imp for imp in other_imports if imp]
            
            # Build replacement
            result = []
            if other_imports:
                result.append(f"from typing import {', '.join(other_imports)}")
            result.append('''
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired''')
            
            return '\n'.join(result)
        
        # Check if file needs fixing
        if re.search(r'from typing import.*NotRequired', content, re.MULTILINE):
            # First handle multi-import cases
            content = re.sub(pattern2, replace_multi_import, content, flags=re.MULTILINE)
            
            # Then handle single import cases
            content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def main():
    """Main function to fix all Python files."""
    # Get all Python files in protocol directory
    protocol_dir = Path('pydoll/protocol')
    if not protocol_dir.exists():
        print("Protocol directory not found")
        return
    
    py_files = list(protocol_dir.rglob('*.py'))
    
    fixed_count = 0
    for py_file in py_files:
        if fix_notrequired_import(py_file):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")

if __name__ == '__main__':
    main() 