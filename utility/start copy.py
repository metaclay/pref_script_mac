#!/usr/bin/env python3

import os
import sys
import shutil
import platform
from pathlib import Path

def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def copy_documents():
    # Define network source
    network_source = r"\\192.168.1.20\CLAYNET\asset\_CLAYSETUP\script"
    mac_source = "/Volumes/CLAYNET/asset/_CLAYSETUP/script"

    system = platform.system()
    source = network_source if system == "Windows" else mac_source

    local_documents = Path.home() / "Documents/preferences/script"
    os.makedirs(local_documents, exist_ok=True)

    if not os.path.exists(source):
        print(f"❌ Source path not found: {source}")
        return

    print(f"✅ Copying from {source} → {local_documents}")

    # Walk through source folder recursively
    for root, dirs, files in os.walk(source):
        # Determine relative path from source root
        rel_path = os.path.relpath(root, source)
        target_root = os.path.join(local_documents, rel_path)

        # Ensure target directories exist
        os.makedirs(target_root, exist_ok=True)

        # Copy files one by one
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_root, file)
            if os.path.exists(dest_file):
                print(f"⚠️ Skipping existing file: {dest_file}")
            else:
                shutil.copy2(src_file, dest_file)
                print(f"📄 Copied file: {dest_file}")

if __name__ == "__main__":
    clear_screen()
    print("CLAY STARTUP\n\n")

    answer = input("Run startup code? (y/N): ").strip().lower()
    if answer != "y":
        print("❌ Aborted by user.")
        sys.exit(0)

    copy_documents()
    print("\n✅ Done.")
    input("Press Enter to exit...")
