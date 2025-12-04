import subprocess

# Path to Nuke executable
NUKE = "/Applications/Nuke15.1v2/Nuke15.1v2.app/Contents/MacOS/Nuke15.1"

# Max Nuke instances running at the same time
max_nuke_instance = 5

# Path to your list of .nk files
FILE_LIST = "_file_list.txt"


def read_file_list(path):
    """Read list of nk files from _file_list.txt."""
    files = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                files.append(line)
    return files


def confirm_file_list(files):
    """Show list summary and ask user if they want to continue."""

    print("\n====================================")
    print(" Nuke Batch Loader Summary")
    print("====================================")

    print(f"Source file list       : {FILE_LIST}")
    print(f"Max Nuke instances     : {max_nuke_instance}")
    print(f"Total NK files found   : {len(files)}")

    print("\nPreview of files:")
    preview_count = min(10, len(files))
    for f in files[:preview_count]:
        print(" -", f)

    if len(files) > preview_count:
        print(f"... and {len(files) - preview_count} more.")

    answer = input("\nProceed with processing? (y/n): ").strip().lower()

    return answer == "y"


def open_nuke_batch(batch):
    """Open a batch of nk files and wait until all Nuke instances close."""
    processes = []

    for nk_file in batch:
        print(f"Launching Nuke: {nk_file}")
        p = subprocess.Popen([NUKE, nk_file])
        processes.append(p)

    print("Waiting for all Nuke instances in this batch to close...")

    for p in processes:
        p.wait()

    print("Batch completed.\n")


def main():
    nk_files = read_file_list(FILE_LIST)

    if not nk_files:
        print("No nk files found in _file_list.txt")
        return

    # Confirm before running
    if not confirm_file_list(nk_files):
        print("Aborted by user.")
        return

    # Process files in batches
    for i in range(0, len(nk_files), max_nuke_instance):
        batch = nk_files[i:i + max_nuke_instance]
        print(f"=== Starting batch {i//max_nuke_instance + 1} ===")
        open_nuke_batch(batch)

    print("All batches complete.")


if __name__ == "__main__":
    main()
