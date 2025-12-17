#!/usr/bin/env python3

import os
import sys
import shutil
import platform
import subprocess
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
        rel_path = os.path.relpath(root, source)
        target_root = os.path.join(local_documents, rel_path)

        os.makedirs(target_root, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(target_root, file)
            if os.path.exists(dest_file):
                print(f"⚠️ Skipping existing file: {dest_file}")
            else:
                shutil.copy2(src_file, dest_file)
                print(f"📄 Copied file: {dest_file}")

def mac_post_tasks():
    """Extra setup only for macOS"""
    home = Path.home()
    script_boot = home / "Documents/preferences/script/boot"
    #changes_made = False

    # 1. Copy .zshrc to home (~/.zshrc) if not exists
    zshrc_src = script_boot / ".zshrc"
    zshrc_dest = home / ".zshrc"
    if zshrc_src.exists():
        if zshrc_dest.exists():
            print(f"⚠️ Skipping .zshrc copy: {zshrc_dest} already exists")
        else:
            shutil.copy2(zshrc_src, zshrc_dest)
            print(f"✅ Copied {zshrc_src} → {zshrc_dest}")
            #changes_made = True
    else:
        print(f"⚠️ .zshrc not found in {script_boot}")

    # 2. Add projectvol.command to login items if not already added
    projectvol = script_boot / "projectvol.command"
    if projectvol.exists():
        try:
            check_cmd = [
                "osascript", "-e",
                'tell application "System Events" to get the name of every login item'
            ]
            result = subprocess.check_output(check_cmd, text=True)
            if "projectvol.command" in result:
                print("⚠️ Login item already exists: projectvol.command")
            else:
                add_cmd = [
                    "osascript", "-e",
                    f'tell application "System Events" to make login item at end with properties {{path:"{projectvol}", hidden:false}}'
                ]
                subprocess.run(add_cmd, check=True)
                print(f"✅ Added login item: {projectvol}")
                #changes_made = True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to add login item: {e}")
    else:
        print(f"⚠️ projectvol.command not found in {script_boot}")

    # 3. Ask for logout if changes were made
    # /if changes_made:
    answer = input("\n⚠️ Changes will take effect after logout.\nLogout now? (y/N): ").strip().lower()
    if answer == "y":
        print("🔄 Logging out...")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to log out'])
    else:
        print("⏭ Skipped logout. Please log out manually later.")



if __name__ == "__main__":
    clear_screen()
    print("CLAY STARTUP\n\n")

    answer = input("Run startup code? (y/N): ").strip().lower()
    if answer != "y":
        print("❌ Aborted by user.")
        sys.exit(0)

    copy_documents()

    if platform.system() == "Darwin":  # macOS check
        mac_post_tasks()

    print("\n✅ Done.")
    input("Press Enter to exit...")
