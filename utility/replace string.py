#!/usr/bin/env python3
"""
Batch text replacement tool

This script will:
- Read file paths from 'file_list.txt'
- For each existing file:
    • Create a .bak backup
    • Replace all occurrences of 'xxx' with 'YYY'
    • Save the updated file in-place
- Skip missing files safely
- Print per-file status messages

⚠️ Intended for text-based files (e.g. Nuke .nk scripts)
⚠️ Changes are irreversible unless using the .bak backups
"""

from pathlib import Path
import shutil

# =========================
# CONFIGURATION
# =========================
LIST_FILE = "file_list.txt"
OLD = "xxx"
NEW = "YYY"

# =========================
# STARTUP INFO (PRINT ONCE)
# =========================
print("=" * 60)
print("Batch Replace Tool")
print("- Reads file paths from:", LIST_FILE)
print(f"- Replaces text      : '{OLD}' → '{NEW}'")
print("- Creates backup     : *.bak")
print("- Files are modified in-place")
print("=" * 60)
print()

# =========================
# PROCESS FILES
# =========================
with open(LIST_FILE, "r", encoding="utf-8") as f:
    paths = [line.strip() for line in f if line.strip()]

for path_str in paths:
    path = Path(path_str)

    if not path.exists():
        print(f"❌ File not found: {path}")
        continue

    try:
        text = path.read_text(encoding="utf-8")
        new_text = text.replace(OLD, NEW)

        if text == new_text:
            print(f"⚠️ No change needed: {path}")
            continue

        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        path.write_text(new_text, encoding="utf-8")

        print(f"✅ Updated: {path}")
        print(f"   ↳ Backup: {backup}")

    except Exception as e:
        print(f"❌ Error processing {path}: {e}")
