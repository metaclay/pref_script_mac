#!/usr/bin/env python3

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path


def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")


def get_source_path() -> str:
    """
    New locations:
      - Windows: \\192.168.1.20\CLAYNET\asset\_CLAYNET_SETUP\scripts\win\script\
      - macOS:   /Volumes/CLAYNET/asset/_CLAYNET_SETUP/scripts/mac/script/
    """
    server_ip = "192.168.1.20"

    win_base = r"CLAYNET\asset\_CLAYNET_SETUP\scripts"
    mac_base = "CLAYNET/asset/_CLAYNET_SETUP/scripts"

    win_source = rf"\\{server_ip}\{win_base}\win\script"
    mac_source = f"/Volumes/{mac_base}/mac/script"

    return win_source if platform.system() == "Windows" else mac_source


def copy_documents():
    source = get_source_path()

    local_documents = Path.home() / "Documents/preferences/script"
    local_documents.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(source):
        print(f"❌ Source path not found: {source}")
        return

    print(f"✅ Copying from {source} → {local_documents}")

    # Folders to skip entirely
    skip_folders = {
        "_CCC SafetyNet",
        "bak",
        "_bak",
        "unsorted",
        "temp",
    }

    for root, dirs, files in os.walk(source):

        # 🔥 Prevent os.walk from entering skipped folders
        dirs[:] = [d for d in dirs if d not in skip_folders]

        rel_path = os.path.relpath(root, source)
        target_root = local_documents / rel_path
        target_root.mkdir(parents=True, exist_ok=True)

        for file in files:
            src_file = os.path.join(root, file)
            dest_file = target_root / file

            if dest_file.exists():
                print(f"⚠️ Skipping existing file: {dest_file}")
            else:
                shutil.copy2(src_file, dest_file)
                print(f"📄 Copied file: {dest_file}")


def mac_post_tasks():
    """Extra setup only for macOS"""
    home = Path.home()
    script_boot = home / "Documents/preferences/script/boot"

    # 1. Copy .zshrc to home (~/.zshrc) if not exists
    zshrc_src = script_boot / ".zshrc"
    zshrc_dest = home / ".zshrc"
    if zshrc_src.exists():
        if zshrc_dest.exists():
            print(f"⚠️ Skipping .zshrc copy: {zshrc_dest} already exists")
        else:
            shutil.copy2(zshrc_src, zshrc_dest)
            print(f"✅ Copied {zshrc_src} → {zshrc_dest}")
    else:
        print(f"⚠️ .zshrc not found in {script_boot}")

    # 2. Add claynet.command to login items if not already added
    claynet = script_boot / "claynet.command"
    if claynet.exists():
        try:
            check_cmd = [
                "osascript", "-e",
                'tell application "System Events" to get the name of every login item'
            ]
            result = subprocess.check_output(check_cmd, text=True)

            if "claynet.command" in result:
                print("⚠️ Login item already exists: claynet.command")
            else:
                add_cmd = [
                    "osascript", "-e",
                    f'tell application "System Events" to make login item at end with properties {{path:"{claynet}", hidden:false}}'
                ]
                subprocess.run(add_cmd, check=True)
                print(f"✅ Added login item: {claynet}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to add login item: {e}")
    else:
        print(f"⚠️ claynet.command not found in {script_boot}")

    answer = input("\n⚠️ Changes will take effect after logout.\nLogout now? (y/N): ").strip().lower()
    if answer == "y":
        print("🔄 Logging out...")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to log out'])
    else:
        print("⏭ Skipped logout. Please log out manually later.")


def main():
    clear_screen()
    print("CLAY STARTUP\n\n")

    answer = input("Run startup code? (y/N): ").strip().lower()
    if answer != "y":
        print("❌ Aborted by user.")
        sys.exit(0)

    copy_documents()

    if platform.system() == "Darwin":
        mac_post_tasks()

    print("\n✅ Done.")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
