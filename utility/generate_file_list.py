import os
import re
import platform
from pathlib import Path


# -----------------------------------
# Configuration
# -----------------------------------

# MATCH_LIST mode:
# 0 = exact match
# 1 = start with
# 2 = end with
# 3 = any (contain)
MATCH_MODE = 1

# ITEMS
# 1 = file
# 2 = folder
# 3 = file or folder
ITEM = 2

MATCH_MODE_LABELS = {
    0: "Exact match",
    1: "Starts with",
    2: "Ends with",
    3: "Contains (anywhere)"
}

ITEM_LABELS = {1: "Files", 2: "Folders", 3: "Files & Folders"}

VERSION = "1"
IGNORE_CASE = 1

# Configure Path for specific OS
SYSTEM = platform.system()
if SYSTEM == "Darwin":  # macOS
    FOLDER = Path("~/Desktop/PROJECTVOL/projects/COLT/project/nuke").expanduser()
elif SYSTEM == "Windows":
    FOLDER = Path("D:/CLAY_EXT/.__USERS__/andi/.__CLAY__/PROJECTVOL_SRC/projects/COLT/project/nuke").expanduser()
else:
    raise RuntimeError("Unsupported OS")


# leave this empty if don't want exact match to any item on this list.
MATCH_LIST = [
"CLT_NTR_0107_005",
"CLT_NTR_0107_140",
"CLT_CAF_0114_330",
]

# --- New Pattern Variables (All must match - AND operation) ---
# For example: file must start with CLT_ AND end with _draft AND contain v001
START_WITH = ["CLT"]        # Filename must start with ANY of these -> example : ["CLT_"]   
END_WITH = []       # Filename must end with ANY of these (excluding extension) -> example : ["v001"]  
CONTAIN = []            # Filename must contain ANY of these
# -----------------------------

# output_file = os.path.expanduser("~/Documents/preferences/script/utility/_file_list.txt")
OUTPUT_FILE = Path.home() / "Documents/preferences/script/utility/_file_list.txt"


# Exclusion patterns
EXCLUDE_FILE_PATTERNS = ["annotations"]        # filenames containing these -> example : ["annotations"] 
EXCLUDE_FOLDER_PATTERNS = ["annotations", "archives", "users", "_bak"]      # folders containing these -> example : ["annotations", "archives", "users", "_bak"]  
EXCLUDE_FILE_ENDINGS = ["~"]                   # filenames ending with these -> example : ["~"]  
EXCLUDE_AUTOSAVE_REGEX = re.compile(r'autosave\d*$')   # ignore autosave1, autosave10, etc.

# Include-only extensions (only these files will be scanned)
INCLUDE_EXTENSIONS = [".nk"]                   # <-- add more if needed
# -----------------------------------


def match_by_mode(filename, patterns, mode, ignore_case=True):
    """
    Match filename against patterns based on mode.
    mode:
      0 = exact
      1 = startswith
      2 = endswith
      3 = contains
    """
    if ignore_case:
        filename = filename.lower()
        patterns = [p.lower() for p in patterns]

    if mode == 0:      # exact
        return filename in patterns
    elif mode == 1:    # starts with
        return any(filename.startswith(p) for p in patterns)
    elif mode == 2:    # ends with
        return any(filename.endswith(p) for p in patterns)
    elif mode == 3:    # contains
        return any(p in filename for p in patterns)
    else:
        raise ValueError(f"Invalid MATCH_MODE: {mode}")


def search_files(folder_path, start_with=[], end_with=[], contain=[],
                 write_output=False, ignore_case=1):

    matched_items = []

    for root, dirs, files in os.walk(folder_path):
        root = Path(root)

        # -------------------------------
        # Skip excluded folders (walk control)
        # -------------------------------
        dirs[:] = [
            d for d in dirs
            if not any(ex.lower() in d.lower() for ex in EXCLUDE_FOLDER_PATTERNS)
        ]

        # ===============================
        # FOLDER MATCHING
        # ===============================
        if ITEM in (2, 3):
            for d in dirs:
                name = d.lower() if ignore_case else d

                is_match = True

                if start_with and not any(name.startswith(p.lower() if ignore_case else p) for p in start_with):
                    is_match = False

                if is_match and end_with and not any(name.endswith(p.lower() if ignore_case else p) for p in end_with):
                    is_match = False

                if is_match and contain and not any((p.lower() if ignore_case else p) in name for p in contain):
                    is_match = False

                if is_match and MATCH_LIST:
                    if not match_by_mode(name, MATCH_LIST, MATCH_MODE, ignore_case):
                        is_match = False

                if is_match:
                    matched_items.append(str(root / d))

        # ===============================
        # FILE MATCHING
        # ===============================
        if ITEM in (1, 3):
            for filename in files:
                fname = filename.lower() if ignore_case else filename

                # -------------------------------
                # File pre-filters
                # -------------------------------
                if INCLUDE_EXTENSIONS:
                    if not any(fname.endswith(ext.lower() if ignore_case else ext) for ext in INCLUDE_EXTENSIONS):
                        continue

                if any(fname.endswith(end.lower() if ignore_case else end) for end in EXCLUDE_FILE_ENDINGS):
                    continue

                if EXCLUDE_AUTOSAVE_REGEX.search(fname):
                    continue

                if any((ex.lower() if ignore_case else ex) in fname for ex in EXCLUDE_FILE_PATTERNS):
                    continue

                # -------------------------------
                # Pattern matching
                # -------------------------------
                is_match = True
                base_name, _ = os.path.splitext(fname)

                if start_with and not any(fname.startswith(p.lower() if ignore_case else p) for p in start_with):
                    is_match = False

                if is_match and end_with and not any(base_name.endswith(p.lower() if ignore_case else p) for p in end_with):
                    is_match = False

                if is_match and contain and not any((p.lower() if ignore_case else p) in fname for p in contain):
                    is_match = False

                if is_match and MATCH_LIST:
                    if not match_by_mode(fname, MATCH_LIST, MATCH_MODE, ignore_case):
                        is_match = False

                if is_match:
                    matched_items.append(str(root / filename))

    # -------------------------------
    # Output
    # -------------------------------
    if write_output:
        try:
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, "w") as f:
                for item in matched_items:
                    f.write(item + "\n")
            print(f"✔ Output written to {OUTPUT_FILE}")
        except Exception as e:
            print(f"✘ Failed to write file: {e}")

    return matched_items


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":
    


    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    print(" -----------------------------------")
    print()
    print("  GENERATE FILE LIST")
    print(f"  ver : {VERSION}")
    print()
    print(f"  Searching in folder: {FOLDER}"  )
    print(f"  Output File: {OUTPUT_FILE}"  )
    print()
    print(f"  Use MATCH LIST : {'Yes' if MATCH_LIST else 'No'}")
    print(f"  Match Mode: {MATCH_MODE} - {MATCH_MODE_LABELS.get(MATCH_MODE, 'Unknown')}")
    print(f"  Start With (OR logic): {START_WITH if START_WITH else 'Any'}")
    print(f"  End With (OR logic): {END_WITH if END_WITH else 'Any'} (excluding extension)")
    print(f"  Contain (OR logic): {CONTAIN if CONTAIN else 'Any'}")
    print(f"  Item Type: {ITEM} ({ITEM_LABELS.get(ITEM)})")
    print()
    print(" -----------------------------------")
    print("\nFile must satisfy **ALL** (AND logic) of the non-empty criteria above.")
    if MATCH_LIST :
        print()
        print("   Also pattern must match one of item in this list : ")
        for i in MATCH_LIST:
            print("  >  "+i)
    print()
    
    answer = input("Proceed? (Y/n): ").strip().lower()
    if answer not in ("", "y"):
        print("Cancelled.")
        exit()

    results = search_files(
        FOLDER,
        start_with=START_WITH,
        end_with=END_WITH,
        contain=CONTAIN,
        write_output=True,
        ignore_case=IGNORE_CASE
    )

    print("\nMatched files:")
    for f in results:
        print(f)

    print(f"\nTotal matched files: **{len(results)}**")