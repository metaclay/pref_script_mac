import os
import re

# -----------------------------------
# Configuration
# -----------------------------------
folder = "/Volumes/CLAY_EXT/.__USERS__/andi/.__CLAY__/PROJECTVOL_SRC/projects/COLT/project/nuke"

# leave this empty if don't want exact match to any item on this list.
match_list = [
"CLT_FNL_140C_112_v001.nk",
"CLT_FNL_140C_115_v001.nk",
"CLT_FNL_140C_118_v001.nk",
"CLT_FNL_140C_124_v001.nk",
"CLT_FNL_140C_127_v001.nk",
"CLT_FNL_140C_130_v001.nk",
"CLT_FNL_140C_133_v001.nk",
"CLT_FNL_140C_136_v001.nk",
"CLT_FNL_140C_139_v001.nk",
"CLT_FNL_140C_142_v001.nk",
"CLT_LOG_0005_155_v001.nk",
"CLT_LOG_0005_160_v001.nk",
"CLT_LOG_0005_170_v001.nk",
"CLT_LOG_0005_190_v001.nk",
"CLT_LOG_0005_195_v001.nk",
"CLT_LOG_0005_200_v001.nk",
"CLT_LOG_0005_230_v001.nk",
"CLT_LOG_0005_235_v001.nk",
"CLT_LOG_0005_240_v001.nk",
"CLT_LOG_0005_245_v001.nk",
"CLT_LOG_0005_275_v001.nk",
"CLT_LOG_0005_305_v001.nk",
"CLT_LOG_0005_325_v001.nk",
"CLT_LOG_0005_330_v001.nk",
"CLT_LOG_0005_335_v001.nk",
]

# --- New Pattern Variables (All must match - AND operation) ---
# For example: file must start with CLT_ AND end with _draft AND contain v001
start_with = ["CLT_"]        # Filename must start with ANY of these
end_with = ["v001"]       # Filename must end with ANY of these (excluding extension)
contain = []            # Filename must contain ANY of these
# -----------------------------

output_file = os.path.expanduser("~/Documents/preferences/script/utility/_file_list.txt")

# Exclusion patterns
exclude_file_patterns = ["annotations"]        # filenames containing these
exclude_folder_patterns = ["annotations", "archives", "users", "_bak"]      # folders containing these
exclude_file_endings = ["~"]                   # filenames ending with these
exclude_autosave_regex = re.compile(r'autosave\d*$')   # ignore autosave1, autosave10, etc.

# Include-only extensions (only these files will be scanned)
include_extensions = [".nk"]                   # <-- add more if needed
# -----------------------------------


def search_files(folder_path, start_with=[], end_with=[], contain=[], write_output=False):
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

        # -------------------------------
        # Skip excluded folders
        # -------------------------------
        dirs[:] = [
            d for d in dirs
            if not any(ex in d for ex in exclude_folder_patterns)
        ]

        for filename in files:
            
            # ----------------------------------
            # Pre-filter checks
            # ----------------------------------
            
            # Include-only extension rule
            if include_extensions:
                if not any(filename.lower().endswith(ext.lower()) for ext in include_extensions):
                    continue

            # Skip file ending exclusions (like '~')
            if any(filename.endswith(end) for end in exclude_file_endings):
                continue

            # Skip autosave files (autosave1, autosave10, autosave99, etc)
            if exclude_autosave_regex.search(filename):
                continue

            # Skip filenames containing excluded patterns
            if any(ex in filename for ex in exclude_file_patterns):
                continue
                
            # ----------------------------------
            # Pattern match logic (The key change for AND operation)
            # ----------------------------------
            
            # Start with the assumption that the file matches
            is_match = True
            base_name, extension = os.path.splitext(filename)

            # 1. Start with match (Fail if list is not empty AND file doesn't match any pattern)
            if start_with:
                if not any(filename.startswith(p) for p in start_with):
                    is_match = False
            
            # If it already failed, move to the next file (optimization)
            if not is_match:
                continue

            # 2. End with match (excluding extension) (Fail if list is not empty AND file doesn't match any pattern)
            if end_with:
                if not any(base_name.endswith(p) for p in end_with):
                    is_match = False

            # If it already failed, move to the next file (optimization)
            if not is_match:
                continue
                
            # 3. Contain match (Fail if list is not empty AND file doesn't match any pattern)
            if contain:
                if not any(p in filename for p in contain):
                    is_match = False

            if match_list :
                if filename not in match_list :
                    is_match = False

           
                
            # If the file passed all the checks (is_match remains True), append it
            if is_match:
                matched_files.append(os.path.join(root, filename))

    # Optional output to file
    if write_output:
        try:
            with open(output_file, "w") as f:
                for item in matched_files:
                    f.write(item + "\n")
            print(f"✔ Output written to **{output_file}**")
        except Exception as e:
            print(f"✘ Failed to write file: {e}")

    return matched_files


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":

    print(f"Searching in folder: {folder}"  )
    print(f"Output File: {output_file}"  )

    print()
    print(" -----------------------------------")
    print(f"  Start With (OR logic): {start_with if start_with else 'Any'}")
    print(f"  End With (OR logic): {end_with if end_with else 'Any'} (excluding extension)")
    print(f"  Contain (OR logic): {contain if contain else 'Any'}")
    print(" -----------------------------------")
    print("\nFile must satisfy **ALL** (AND logic) of the non-empty criteria above.")
    if match_list :
        print()
        print("   Also pattern must match one of item in this list : ")
        for i in match_list:
            print("  >  "+i)
    print()
    
    answer = input("Proceed? (Y/n): ").strip().lower()
    if answer not in ("", "y"):
        print("Cancelled.")
        exit()

    results = search_files(
        folder,
        start_with=start_with,
        end_with=end_with,
        contain=contain,
        write_output=True
    )

    print("\nMatched files:")
    for f in results:
        print(f)

    print(f"\nTotal matched files: **{len(results)}**")