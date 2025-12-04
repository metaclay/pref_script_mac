import os
import subprocess
import re


# ------------------------ EDIT BELOW THIS LINE ------------------------

# Full path to your Nuke executable
NUKE = "/Applications/Nuke15.1v2/Nuke15.1v2.app/Contents/MacOS/Nuke15.1"

# Root folder to scan recursively
SCRIPT_DIR = "/Users/andi/Desktop/PROJECTVOL/projects/COLT/project/nuke"

# Ignore These Subfolders
IGNORE_FOLDERS = [
    "annotations",
    "_bak"
]

# Only render these base names
TARGET_FILES = [
"CLT_CAF_0111_115_v001",
"CLT_CAF_0111_160_v001",
"CLT_CAF_0111_165_v001",
"CLT_CAF_0111_170_v001",
"CLT_CAF_0111_175_v001",
"CLT_CAF_0111_180_v001",
"CLT_CAF_0113_195_v001",
"CLT_CAF_0113_200_v001",
"CLT_CAF_0113_210_v001",
"CLT_CAF_0113_220_v001",
"CLT_CAF_0113_250_v001",
"CLT_CAF_0113_255_v001",
"CLT_CAF_0113_260_v001",
"CLT_CAF_0113_265_v001",
"CLT_CAF_0114_295_v001",
"CLT_CAF_0114_320_v001",
"CLT_CAF_108B_015_v001",
"CLT_CAF_108B_020_v001",
"CLT_CAF_108B_025_v001",
"CLT_CAF_108B_030_v001",
"CLT_CAF_108B_035_v001",
"CLT_CAF_108B_045_v001",
"CLT_CAF_108B_050_v001",
"CLT_CAF_108B_055_v001",
"CLT_CAF_108B_065_v001",
"CLT_CAF_108B_080_v001",
"CLT_CAF_108B_085_v001",
"CLT_CAM_0017_075_v001",
"CLT_CAM_0017_080_v001",
"CLT_CAM_0017_085_v001",
"CLT_CAM_0017_105_v001",
"CLT_CAM_0017_125_v001",
"CLT_CAM_0017_153_v001",
"CLT_CAM_0017_205_v001",
"CLT_CAM_0017_210_v001",
"CLT_CAM_0017_215_v001",
"CLT_CAM_0017_225_v001",
"CLT_CAM_0017_230_v001",
"CLT_CAM_0017_235_v001",
"CLT_CAM_0017_240_v001",
"CLT_CAM_0017_245_v001",
"CLT_CAM_0017_250_v001",
"CLT_CAM_0017_255_v001",
"CLT_CAM_0017_270_v001",
"CLT_CAM_0017_310_v001",
"CLT_CAM_0017_315_v001",
"CLT_CAM_0017_325_v001",
"CLT_CAM_0017_330_v001",
"CLT_LOG_0005_130_v001",
"CLT_LOG_0005_135_v001",
"CLT_LOG_0005_140_v001",
"CLT_LOG_0005_145_v001",
"CLT_LOG_0005_150_v001",
"CLT_LOG_0005_165_v001",
"CLT_NTR_0107_015_v001",
"CLT_NTR_0107_070_v001",
"CLT_NTR_0107_075_v001",
"CLT_NTR_0107_085_v001",
"CLT_NTR_0107_102_v001",
"CLT_NTR_0107_130_v001",
"CLT_NTR_0107_135_v001",
"CLT_NTR_0110_285_v001",
"CLT_NTR_0110_290_v001",
"CLT_NTR_0110_305_v001",
"CLT_NTR_0110_315_v001",
"CLT_NTR_0110_325_v001",
"CLT_NTR_0110_335_v001",
"CLT_NTR_0110_340_v001",
"CLT_NTR_0110_345_v001",
"CLT_NTR_0110_350_v001"
]

# ------------------------------------------------------------------------

while True:
    print("Select Render Mode :")
    print("0 - Render v000")
    print("1 - Render Final  (default)")
    print("2 - Render Review")
    print("3 - Render Review EXR")

    choice = input("Enter your choice (0/1/2/3) or press Enter for default: ")

    # Default on Enter
    if choice.strip() == "":
        choice = 1
        break

    # Accept only 0, 1, 2
    if choice in ("0", "1", "2", "3"):
        choice = int(choice)
        break

    print("Invalid input. Please enter 0, 1, 2, 3 or press Enter.\n")



# Target Write node
if choice == 0:
    WRITE_NODE = "_RENDER_V0"
elif choice == 1:
    WRITE_NODE = "_RENDER_FINAL"
elif choice == 2:
    WRITE_NODE = "_RENDER_REVIEW"
elif choice == 3:
    WRITE_NODE = "_RENDER_REVIEW_EXR"    
else:
    print("Invalid choice. Defaulting to Render v000.")
    exit(1)

print()
print(f"Selected Render Mode ==> {WRITE_NODE}\n")
print("Do you want to proceed with the batch render? (enter to continue or any other key to cancel): ")
confirm = input().strip().lower()
if confirm != "":
    print("Batch render cancelled by user.")
    exit(0)




def is_autosave(path):
    return re.search(r"\.nk\.autosave\d+$", path.lower()) is not None


def should_ignore(path):
    lower = path.lower()

    if lower.endswith("~"):
        return True

    if is_autosave(path):
        return True
    
    for folder in IGNORE_FOLDERS:  
        if folder in lower.split(os.sep):
            return True      

    return False


def basename_no_ext(path):
    base = os.path.basename(path)
    return base[:-3] if base.endswith(".nk") else base


# ---------------------------------------------------------
# 🔍 FIND VALID SCRIPTS RECURSIVELY
# ---------------------------------------------------------
nk_files = []
found_targets = set()
missing_targets = []

print("Searching for Nuke scripts in:", SCRIPT_DIR)
print("Processing...")
print()
for root, dirs, files in os.walk(SCRIPT_DIR):
    for f in files:
        if f.endswith(".nk"):
            full_path = os.path.join(root, f)

            if should_ignore(full_path):
                # print(f"⏭️  Ignored: {full_path}")
                continue

            base = basename_no_ext(full_path)

            if base in TARGET_FILES:
                nk_files.append(full_path)
                found_targets.add(base)
            else:
                #print(f"⏭️  Not in list: {full_path}")
                None

# Detect missing .nk files that were expected but never found
for target in TARGET_FILES:
    if target not in found_targets:
        missing_targets.append(target)


print()
for nk in nk_files:
    print(f"   - {nk}")
print()
print("Search "+ str(len(TARGET_FILES))+" Files in "+ SCRIPT_DIR)
print(f"\n🔍 Found {len(nk_files)} script(s) to render.\n")
print()
print("Do you want to proceed with the batch render? (enter to continue or any other key to cancel): ")
confirm = input().strip().lower()
if confirm != "":
    print("Batch render cancelled by user.")
    exit(0)

# ---------------------------------------------------------
# 🚀 RENDER EACH SCRIPT (uses internal frame range)
# ---------------------------------------------------------

failed_renders = []

for nk in nk_files:
    cmd = [
        NUKE,
        "-x",
        "-X", WRITE_NODE,
        nk
    ]

    print(f"🚀 Rendering: {nk}")
    print("🔧 Command:", " ".join(cmd))

    # subprocess.run returns returncode → non-zero means failure
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"❌ FAILED: {nk}")
        failed_renders.append(nk)
    else:
        print(f"✅ SUCCESS: {nk}")


# ---------------------------------------------------------
# 📊 FINAL REPORT
# ---------------------------------------------------------
print("\n================= FINAL REPORT =================")

if missing_targets:
    print("\n❗ Missing Nuke scripts (not found on disk):")
    for m in missing_targets:
        print(f"   - {m}")
else:
    print("\n✅ All target scripts were found.")

if failed_renders:
    print("\n❌ Scripts that FAILED to render:")
    for f in failed_renders:
        print(f"   - {f}")
else:
    print("\n✅ All scripts rendered successfully!")

print("\n=================================================\n")
