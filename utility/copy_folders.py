import os
import shutil
import sys

print(" COPYING FOLDER USING LIST")
print("---------------------------")
print()

if len(sys.argv) < 3:
    print("Usage: python script.py argumen1 argumen2")
    sys.exit(1)


source_parent = os.path.expanduser(sys.argv[1])
target_parent = os.path.expanduser(sys.argv[2])
overwrite = 1 #overwrite if exist.

# list of folder names
# folders_to_copy = [
# "TSS_110_051_0011",
# "TSS_110_051_0055"
# ]  
#
folders_to_copy = [
"vvv"
]  

if ( len(folders_to_copy) == 0 ) :
    print("The list is empty. Doing nothing.")
    sys.exit(1)

print(f"🔁 Copying folders...")
print(f"📁 Base Source Folder: {source_parent}")
print(f"📁 Base Target Folder: {target_parent}")
print()
if overwrite :
    print("Overwrite if exists")
else :
    print("Ask if exists")


skipall = 0
print("--------------------------------------")
print("")

for folder in folders_to_copy:
    source_path = os.path.join(source_parent, folder)
    target_path = os.path.join(target_parent, folder)

    # Check if source folder exists
    if not os.path.exists(source_path) :
        print(f"⚠️  Source folder not found: {folder} — skipping.")
        continue

    # Check if target folder exists
    if not overwrite :
        
        if os.path.exists(target_path):
            if skipall :
                print(f"❌ Skipping '{folder}' ")
                continue
            else :
                confirm = input(f"❓ Target folder '{folder}' already exist. Skip it? (y/n or Y to skip all): ").strip()
                if confirm == 'y':
                    print(f"❌ Skipping '{folder}'")
                    continue
                else :
                    if confirm == 'Y' :
                        print(f"❌ Skipping '{folder}' ")
                        skipall = 1
                        continue
                    


    # Copy the folder
    try:
        shutil.copytree(src=source_path, dst=target_path, dirs_exist_ok=True)
        print(f"✅ Copied: {folder}")
    except Exception as e:
        print(f"❌ Error copying '{folder}': {e}")
