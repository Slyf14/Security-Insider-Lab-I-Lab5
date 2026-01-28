"""
Clean SRAM PUF capture files and removing garbage characters
"""

import os
import re


def clean_file(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
    
    text = content.decode('utf-8', errors='replace')
    match = re.search(r'[0-9A-Fa-f]{2} [0-9A-Fa-f]{2} [0-9A-Fa-f]{2} [0-9A-Fa-f]{2}', text)
    
    if match:
        start_pos = match.start()
        clean_content = text[start_pos:]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_content)
        
        return True
    return False


def clean_directory(directory):
    cleaned = 0
    failed = 0
    
    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        
        if not os.path.isfile(filepath):
            continue
        if filename.endswith(('.py', '.c', '.md')):
            continue
        
        print(f"Cleaning: {filename}...", end=" ")
        
        if clean_file(filepath):
            print("OK")
            cleaned += 1
        else:
            print("SKIPPED (no valid hex data found)")
            failed += 1
    
    print(f"\nDone! Cleaned {cleaned} files, skipped {failed} files.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        directory = os.path.join(parent_dir, "SRAM_collected_data", "card1")
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        sys.exit(1)
    
    print(f"Cleaning files in: {directory}\n")
    clean_directory(directory)
