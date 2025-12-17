import os
import re
import platform
from pathlib import Path


# -----------------------------------
# Configuration
# -----------------------------------


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
"CLT_FNL_0143_412"
]

# --- New Pattern Variables (All must match - AND operation) ---
# For example: file must start with CLT_ AND end with _draft AND contain v001
START_WITH = ["CLT_"]        # Filename must start with ANY of these -> example : ["CLT_"]   
END_WITH = ["v001"]       # Filename must end with ANY of these (excluding extension) -> example : ["v001"]  
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


def search_files(folder_path, start_with=[], end_with=[], contain=[], write_output=False, ignore_case=1):
    """
    Searches for files in a directory that match ALL of the provided patterns (AND operation).

    Args:
        folder_path (str): The root directory to search.
        start_with (list): List of strings the filename should start with (file must match one).
        end_with (list): List of strings the filename should end with (before extension, file must match one).
        contain (list): List of strings the filename should contain (file must match one).
        write_output (bool): If True, writes results to the output_file.

    Returns:
        list: A list of full paths to the matched files.
    """
    matched_files = []

    for root, dirs, files in os.walk(folder_path):
        root = Path(root)

        # -------------------------------
        # Skip excluded folders
        # -------------------------------
        dirs[:] = [
            d for d in dirs
            if not any(ex in d for ex in EXCLUDE_FOLDER_PATTERNS)
        ]

        for filename in files:
            if ignore_case :
                fname = filename.lower() #ignore case
            else :
                fname = filename

            # ----------------------------------
            # Pre-filter checks
            # ----------------------------------
            
            # Include-only extension rule
            if INCLUDE_EXTENSIONS:
                if not any(fname.endswith(ext.lower() if ignore_case else ext ) for ext in INCLUDE_EXTENSIONS):
                    continue

            # Skip file ending exclusions (like '~')
            if any(fname.endswith(end.lower() if ignore_case else end ) for end in EXCLUDE_FILE_ENDINGS):
                continue

            # Skip autosave files (autosave1, autosave10, autosave99, etc)
            if EXCLUDE_AUTOSAVE_REGEX.search(fname):
                continue

            # Skip filenames containing excluded patterns
            if any((ex.lower() if ignore_case else ex ) in fname for ex in EXCLUDE_FILE_PATTERNS):
                continue
                
            # ----------------------------------
            # Pattern match logic (The key change for AND operation)
            # ----------------------------------
            
            # Start with the assumption that the file matches
            is_match = True
            base_name, extension = os.path.splitext(fname)

            # 1. Start with match (Fail if list is not empty AND file doesn't match any pattern)
            if start_with:
                if not any(fname.startswith(p.lower() if ignore_case else p) for p in start_with):
                    is_match = False
            
            # If it already failed, move to the next file (optimization)
            if not is_match:
                continue

            # 2. End with match (excluding extension) (Fail if list is not empty AND file doesn't match any pattern)
            if end_with:
                if not any(base_name.endswith(p.lower() if ignore_case else p) for p in end_with):
                    is_match = False

            # If it already failed, move to the next file (optimization)
            if not is_match:
                continue
                
            # 3. Contain match (Fail if list is not empty AND file doesn't match any pattern)
            if contain:
                if not any((p.lower() if ignore_case else p) in fname for p in contain):
                    is_match = False

            if MATCH_LIST :
                if fname not in MATCH_LIST :
                    is_match = False

           
                
            # If the file passed all the checks (is_match remains True), append it
            if is_match:
                matched_files.append(os.path.join(root, filename))

    # Optional output to file
    if write_output:
        try:
            with open(OUTPUT_FILE, "w") as f:
                for item in matched_files:
                    f.write(item + "\n")
            print(f"✔ Output written to **{OUTPUT_FILE}**")
        except Exception as e:
            print(f"✘ Failed to write file: {e}")

    return matched_files


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":

    print(f"Searching in folder: {FOLDER}"  )
    print(f"Output File: {OUTPUT_FILE}"  )

    print()
    print(" -----------------------------------")
    print(f"  Start With (OR logic): {START_WITH if START_WITH else 'Any'}")
    print(f"  End With (OR logic): {END_WITH if END_WITH else 'Any'} (excluding extension)")
    print(f"  Contain (OR logic): {CONTAIN if CONTAIN else 'Any'}")
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
        write_output=True
    )

    print("\nMatched files:")
    for f in results:
        print(f)

    print(f"\nTotal matched files: **{len(results)}**")