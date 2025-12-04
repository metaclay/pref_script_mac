import os
import re


# -----------------------------------
# Configuration
# -----------------------------------
folder = "/Volumes/CLAY_EXT/.__USERS__/andi/.__CLAY__/PROJECTVOL_SRC/projects/COLT/project/nuke/FNL"
pattern = "CLT_"
mode = 1    #1 = startswith, 2 = endswith, 3 = substring match, 4 = exact match
output_file = "_file_list.txt"

# Exclusion patterns
exclude_file_patterns = ["annotations"]        # filenames containing these
exclude_folder_patterns = ["annotations", "archives"]      # folders containing these
exclude_file_endings = ["~"]                   # filenames ending with these
exclude_autosave_regex = re.compile(r'autosave\d*$')   # ignore autosave1, autosave10, etc.

# Include-only extensions (only these files will be scanned)
include_extensions = [".nk"]                   # <-- add more if needed
# -----------------------------------


def search_files(folder_path, name_pattern, mode=1, write_output=False):

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
            # Include-only extension rule
            # ----------------------------------
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
            # Pattern match modes
            # ----------------------------------
            if mode == 1 and filename.startswith(name_pattern):
                matched_files.append(os.path.join(root, filename))

            elif mode == 2 and filename.endswith(name_pattern):
                matched_files.append(os.path.join(root, filename))

            elif mode == 3 and name_pattern in filename:
                matched_files.append(os.path.join(root, filename))

            elif mode == 4 and filename == name_pattern:
                matched_files.append(os.path.join(root, filename))

    # Optional output to file
    if write_output:
        try:
            with open(output_file, "w") as f:
                for item in matched_files:
                    f.write(item + "\n")
            print(f"✔ Output written to {output_file}")
        except Exception as e:
            print(f"✘ Failed to write file: {e}")

    return matched_files


# -------------------------------
# Example usage
# -------------------------------
if __name__ == "__main__":

    print(f"Searching in folder: {folder}"  )
    answer = input("Proceed? (Y/n): ").strip().lower()
    if answer not in ("", "y"):
        print("Cancelled.")
        exit()

    results = search_files(
        folder,
        pattern,
        mode,
        write_output=True
    )

    print("Matched files:")
    for f in results:
        print(f)

    print(f"\nTotal matched files: {len(results)}")
