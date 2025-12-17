import os
import sys
import shutil

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

_VERSION = "1"
_SRC  = os.path.expanduser("~/SRC_FOLDER")
_DEST = os.path.expanduser("~/DEST_FOLDER")
_USE_EXTERNAL_FILE_LIST = 0
_FILE_LIST = os.path.expanduser("~/Documents/preferences/script/utility/_file_list.txt")
_OVERWRITE = 0
_DEPTH = 0
_KEEP_TREE = 0
_PRINT_DETAIL = 0

_MATCH_MODE = 1
# 0 = exact
# 1 = start_with
# 2 = end_with
# 3 = any

FOLDERS_TO_COPY = [

"CLT_NTR_0107_005",
"CLT_NTR_0107_140",
"CLT_CAF_0114_330",
]

# -------------------------------------------------
# HEADER
# -------------------------------------------------

# Clear screen
os.system('cls' if os.name == 'nt' else 'clear')

print("\n  COPY FOLDERS")
print(f"  ver. {_VERSION}")
print("  Usage : copy_folders <src> <dst>")
print()
print("------------------------------------------------\n")

match_mode_name = {
    0: "exact",
    1: "start_with",
    2: "end_with",
    3: "any",
}.get(_MATCH_MODE, "unknown")

print(f"🔍 SEARCH DEPTH  : {_DEPTH}")
print(f"🎯 MATCH MODE   : {match_mode_name}")
print(f"🌳 KEEP TREE    : {'YES' if _KEEP_TREE else 'NO'}")
print(f"🧾 DETAIL PRINT : {'YES' if _PRINT_DETAIL else 'NO'}")
print(f"🧾 OVERWRITE : {'YES' if _OVERWRITE else 'NO'}")

# -------------------------------------------------
# ARGUMENT HANDLING
# -------------------------------------------------

src_root  = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else _SRC
dest_root = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else _DEST

# -------------------------------------------------
# SRC / DEST CHECK
# -------------------------------------------------

src_ok  = os.path.exists(src_root)
dest_ok = os.path.exists(dest_root)

print(f"📁 SOURCE ROOT : {src_root} {'✅' if src_ok else '❌'}")
print(f"📁 DEST ROOT   : {dest_root} {'✅' if dest_ok else '❌'}\n")
print("------------------------------------------------\n")

if not src_ok or not dest_ok:
    print("❌ Cannot continue:")
    if not src_ok:
        print("   - Source root does not exist")
    if not dest_ok:
        print("   - Destination root does not exist")
    sys.exit(1)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def match_name(name, pattern, mode):
    if mode == 0:
        return name == pattern
    if mode == 1:
        return name.startswith(pattern)
    if mode == 2:
        return name.endswith(pattern)
    if mode == 3:
        return pattern in name
    return False


def find_folder(base, pattern, max_depth, match_mode):
    base = os.path.abspath(base)
    base_depth = base.count(os.sep)

    for root, dirs, _ in os.walk(base):
        depth = root.count(os.sep) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue

        for d in dirs:
            if match_name(d, pattern, match_mode):
                return os.path.join(root, d)
    return None


def find_existing_dest(dest_root, pattern, match_mode):
    for name in os.listdir(dest_root):
        full = os.path.join(dest_root, name)
        if os.path.isdir(full) and match_name(name, pattern, match_mode):
            return full
    return None

# -------------------------------------------------
# LOAD LIST
# -------------------------------------------------

# print("FOLDERS TO COPY :")
# print("--------------------")
items = []
use_full_path = False

if _USE_EXTERNAL_FILE_LIST:
    print(f"📄 External list file : {_FILE_LIST}")
    if not os.path.exists(_FILE_LIST):
        print("❌ External list not found")
        sys.exit(1)

    with open(_FILE_LIST) as f:
        for line in f:
            p = line.strip()
            if not p:
                continue
            if os.path.isabs(p):
                use_full_path = True
                items.append(os.path.normpath(p))
            else:
                items.append(p)
else:
    items = FOLDERS_TO_COPY[:]

# for i in items:
#     print(i)

if not items:
    print("❌ No folders requested.")
    sys.exit(0)



# -------------------------------------------------
# PREFLIGHT
# -------------------------------------------------

resolved = []
missing_src = []
existing_dst = []
existing_item = []

for item in items:
    if use_full_path:
        src = item
        rel = os.path.relpath(src, src_root)
    else:
        direct = os.path.join(src_root, item)
        if os.path.exists(direct):
            src = direct
            rel = item
        else:
            found = find_folder(src_root, item, _DEPTH, _MATCH_MODE)
            if not found:
                missing_src.append(item)
                continue
            src = found
            rel = os.path.relpath(src, src_root)

    if _KEEP_TREE:
        dst = os.path.join(dest_root, rel)
    else:
        dst = os.path.join(dest_root, os.path.basename(src))

    existing = find_existing_dest(dest_root, os.path.basename(dst), _MATCH_MODE)
    if existing:
        existing_dst.append(existing)
        existing_item.append(item)

    resolved.append((src, dst))

# reset list if overwrite
if _OVERWRITE :
    existing_item = [] 

print(f"\n📦 Requested folders ({len(items)}):")
for i in items:
    print("   " + ("❌" if i in missing_src else ("✅" if i not in existing_item else "⚠️")), i )
print()


# FOUND
print(f"Found {len(resolved)} item(s)")        
if _PRINT_DETAIL:
    for i in resolved:
        print("   -", i[0])
    print()

# MISSING
print(f"Missing ❌ {len(missing_src)} item(s)")   

if _PRINT_DETAIL:
    for i in missing_src:
        print("   -", i)
    print()

# EXIST
print(f"Existing ⚠️ {len(existing_dst)} item(s)")   

if _PRINT_DETAIL:
    for i in existing_dst:
        print("   -", i)
    print()

# VALID
# update resolved to check if exist in target - remove if not overwrite mode
if not _OVERWRITE :
    existing_dst_name = [os.path.basename(i)  for i in existing_dst]

    resolved2 = []
    for i in resolved :
        name = os.path.basename(i[0])
        if name not in existing_dst_name :
            resolved2.append(i)
    resolved = resolved2

print(f"Valid to process ✅ {len(resolved)} item(s)")   
if _PRINT_DETAIL:
    for i in resolved:
        print("   -", i[0])
    print()


# PRINT MORE DETAIL INFO
if len(resolved)>0 :
    if _PRINT_DETAIL:
        # FOUND
        print("-------------------------------")
        print(f"RESULT")
        print(f"KEEP TREE : {"YES" if _KEEP_TREE==1 else "NO"}")
        print(f"OVERWRITE : {_OVERWRITE}")
        print("-------------------------------")
        for i in resolved:
            print(f"🔍 Src : {i[0]}")
            print(f"📦 Dest  : {i[1]}\n")


        



# -------------------------------------------------
# EARLY EXIT
# -------------------------------------------------

if not resolved:
    print("⚠️  NOTHING TO COPY.")
    sys.exit(0)

if not _OVERWRITE and len(existing_dst) == len(resolved):
    print("ℹ️  All folders exist in DEST and overwrite is OFF.")
    sys.exit(0)

# -------------------------------------------------
# CONFIRM
# -------------------------------------------------
print()
if input("Continue? (Y/N): ").strip().lower() not in ("", "y"):
    print("❌ Canceled.")
    sys.exit(0)

print("\n--------------------------------------\n")

# -------------------------------------------------
# COPY
# -------------------------------------------------

total = len(resolved)

for idx, (src, dst) in enumerate(resolved, start=1):

    print(f"📦 Copying #{idx} of #{total} --> {os.path.basename(src)}")

    if os.path.exists(dst) and not _OVERWRITE:
        print(f"⏭️  Skipped (exists): {dst}\n")
        continue

    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"Src : {src}")
        print(f"Dest : {dst}")
        print(f"✅ Successful\n")
    except Exception as e:
        print(f"❌ Error copying {src}: {e}\n")

print("✔ Done.\n")
