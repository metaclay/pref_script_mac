import nuke
import os
import shutil
import sys
import clayproject
import cxsetting
import hashlib
import re
import nukescripts

FILE_LIST = os.path.expanduser("~/Documents/preferences/script/utility/_file_list.txt")

FAILED = []     # (path, reason)
SKIPPED = []    # (path, reason)

MODE = 6
REPLACE_RENDER_GROUP = 1
RENDER_VERSION = 0

NODES_TO_DELETE = [
    "Precomp1"
]

_NODES_V0_ = clayproject._NODES_V0_
_NODES_OUTPUT_ = clayproject._NODES_OUTPUT_
_RENDER_V0_ = clayproject._RENDER_V0_
_RENDER_FINAL_ = clayproject._RENDER_FINAL_

RENAME_MAP = {
    "_src_tc": "_src_tc_",
    "_src_meta": "_src_meta_",
    "_src_ref": "_src_ref_",
    "_src_plate": "_src_plate_",
    "_repos_final": "_repos_final_",
    "_repos_mov": "_repos_mov_",
    "_in_final": "_in_final_",
    "_in_ref": "_in_ref_",
    "_in_plate": "_in_plate_",

}

MODE_DESCRIPTIONS = {
    1: "INTIAL SETUP - CLAYPROJECT NODES CLEANUP",
    2: "CREATE RENDER GROUP" + (" > RENDER V000" if RENDER_VERSION == 0 else " > RENDER FINAL"),
    3: "RENDER " + ("(Non-Modifying)" if REPLACE_RENDER_GROUP == 0 else "") +
       (" > RENDER V000" if RENDER_VERSION == 0 else " > RENDER FINAL"),
    4: "DELETE NODES",
    5: "RESET ROOT CX",
    6: "RENAME NODES",
}

MAX_FILE_LIST = 6
_CHANGE_TOKEN_= "_change_token_"
VERBOSE = 1



def full_scene_hash():
    h = hashlib.md5()
    
    for n in nuke.allNodes(recurseGroups=True):
        h.update(n.Class().encode())
        h.update(n.name().encode())
        knobs = n.writeKnobs(nuke.WRITE_NON_DEFAULT_ONLY)
        h.update(knobs.encode())
    
    return h.hexdigest()

# ----------------------------------------------------
# READ LIST
# ----------------------------------------------------
def read_file_list(path):
    print("\n[READ FILE LIST] Loading:", path)
    files = []

    if not os.path.exists(path):
        print("  ❌ FILE LIST NOT FOUND:", path)
        return files

    try:
        seen = set()
        with open(path, "r") as f:
            for line in f:
                clean = line.strip()
                if clean and clean not in seen:
                    files.append(clean)
                    seen.add(clean)

        print(f"  ✔ Loaded {len(files)} unique file entries.")

    except Exception as e:
        print(f"  ❌ Error reading list: {e}")

    return files


# ----------------------------------------------------
# BACKUP
# ----------------------------------------------------
def backup_original(nk_path):
    print("  --->  Backing up original NK file ...")

    nk_dir = os.path.dirname(nk_path)
    nk_file = os.path.basename(nk_path)
    name, ext = os.path.splitext(nk_file)

    archive_dir = os.path.join(nk_dir, "archives")

    archive_name = nk_file
    counter = 0

    while True:
        if counter == 0:
            archive_path = os.path.join(archive_dir, archive_name)
        else:
            archive_name = f"{name}-{counter:02d}{ext}"
            archive_path = os.path.join(archive_dir, archive_name)

        if not os.path.exists(archive_path):
            break

        counter += 1

    try:
        os.makedirs(archive_dir, exist_ok=True)
        shutil.copy2(nk_path, archive_path)
        print(f"  ✅ Backup saved to: **{archive_path}**")

    except Exception as e:
        print(f"  ❌ Failed to backup file: {e}")
        FAILED.append((nk_path, f"Backup failed: {e}"))


# ----------------------------------------------------
# MODE 1
# ----------------------------------------------------
def initial_setup(nk_path, ignore_skipped=0, ignore_failed=0):

    # RESET CX PARAMETER IF EMPTY
    cxproject = nuke.root().knob('cxproject').value()
    if cxproject =="" :
        print("  Reset CX Parameter ...")
        nuke.root()['cxallreset'].execute()
        return True
    
    None # only load and re-save to trigger nodes_cleanup() when open script


# ----------------------------------------------------
# MODE 2
# ----------------------------------------------------
def create_render_group(nk_path, replace_render_group=0,
                        ignore_skipped=0, ignore_failed=0,
                        render_version=0):

    print("  --->  Running create_render_group procedure ...")
    print()

    initial_setup(nk_path, ignore_skipped=1, ignore_failed=1)

    if render_version == 0:
        render_group_node = _NODES_V0_
    else:
        render_group_node = _NODES_OUTPUT_

    render_group_list = any(n.name().startswith(render_group_node)
                            for n in nuke.allNodes())

    if render_group_list:
        msg = "Node " + render_group_node + " found " + ( "→ Skipping render group creation." if not replace_render_group else "→ OVERWRITING existing render group." )
        print("  ⚠️", msg)

        if not replace_render_group:
            if not ignore_skipped:
                SKIPPED.append((nk_path, msg))
            print(" ⚠️ SKIPPING ...")
            return False

    else:
        print("  ✔ Render group not found. Proceeding with render group creation.")

    try:
        clayproject.clay_shortcut_render(
            replace=replace_render_group,
            render_version=RENDER_VERSION
        )

        print("  ✅ Render group creation is completed successfully.")
        nukescripts.clear_selection_recursive() 
        change_node = nuke.createNode("Dot")
        change_node.setName(_CHANGE_TOKEN_)
        return True

    except ImportError:
        msg = "Render group creation failed: Required module 'cxdef' not found."
        print("  ❌", msg)
        if not ignore_failed:
            FAILED.append((nk_path, msg))
        return False

    except Exception as e:
        msg = f"Render group creation failed: {e}"
        print("  ❌", msg)
        if not ignore_failed:
            FAILED.append((nk_path, msg))
        return False
    
    

# ----------------------------------------------------
# MODE 3
# ----------------------------------------------------
def render(nk_path, render_version=0):
    print("  --->  Running render procedure  ...")

    if render_version == 0:
        render_node_name = _RENDER_V0_
    else:
        render_node_name = _RENDER_FINAL_

    render_node = nuke.toNode(render_node_name)

    render_group_created = False
    check = False

    if not render_node:
        print("  ▶ Render node '" + render_node_name + "' not found. Running create_render_group() setup...")
        render_group_created = create_render_group(
            nk_path,
            replace_render_group=REPLACE_RENDER_GROUP,
            ignore_skipped=1,
            ignore_failed=1,
            render_version=render_version
        )
        check = True

    else:
        if REPLACE_RENDER_GROUP:
            print("  ✔ Render node '" + render_node_name + "' found. Replacing with new one !!!")
            render_group_created = create_render_group(
                nk_path,
                replace_render_group=REPLACE_RENDER_GROUP,
                ignore_skipped=1,
                ignore_failed=1,
                render_version=render_version
            )
            check = True
        else:
            initial_setup(nk_path, ignore_skipped=1, ignore_failed=1)
            print("  ✔ Render node '" + render_node_name + "' found. Starting render.")
            print()

    if check:
        if not render_group_created:
            print("  ❌ create_render_group failed or was skipped. Cannot proceed with render.")
            return False

        render_node = nuke.toNode(render_node_name)

        if not render_node:
            msg = ("Render node '" + render_node_name +
                   "' still not found after running create_render_group(). Aborting render.")
            print("  ❌", msg)
            FAILED.append((nk_path, msg))
            return False

    try:
        first = int(nuke.root().firstFrame())
        last = int(nuke.root().lastFrame())

        nuke.execute(render_node, first, last)

        print(f"  ✅ Render completed successfully for frames {first}-{last}.")

        if render_group_created:
            return True
        else:
            return False

    except Exception as e:
        msg = f"Rendering of '" + render_node_name + f"' failed: {e}"
        print("  ❌", msg)
        FAILED.append((nk_path, msg))
        return False
    None


# ----------------------------------------------------
# MODE 4
# ----------------------------------------------------
def delete_nodes(nk_path, nodes_to_delete):
    print("  --->  Running delete_nodes procedure ...")

    try:
        False

        for node_name in nodes_to_delete:
            node = nuke.toNode(node_name)

            if node:
                nuke.delete(node)
                print(f"  ✅ Deleted node: {node_name}")
                True

            else:
                print(f"  ⚠️ Node not found, skipping: {node_name}")
                SKIPPED.append((nk_path, f"Node not found: {node_name}"))

        return changed

    except Exception as e:
        msg = f"delete_nodes failed: {e}"
        print("  ❌", msg)
        FAILED.append((nk_path, msg))
        return False


# ----------------------------------------------------
# MODE 5
# ----------------------------------------------------
def reset_rootcx(nk_path):
    print("  --->  Executing nuke.root().knob('cxallreset').execute() ...")

    try:
        if nuke.root().knob('cxallreset'):
            nuke.root().knob('cxallreset').execute()
            print("  ✔ 'cxallreset' executed successfully.")
            return True

        else:
            print("  ▶ Warning: 'cxallreset' knob not found on the root node.")
            SKIPPED.append((nk_path, "'cxallreset' knob not found on root"))
            return False

    except Exception as e:
        print(f"  ❌ Failed to execute 'cxallreset': {e}")
        return False


# ----------------------------------------------------
# MODE 6
# ----------------------------------------------------
def rename_nodes(nk_path, rename_map):
    print("  ---> >> Running rename_nodes procedure ...")
    False

    try:
        for old_name, new_name in rename_map.items():
            node = nuke.toNode(old_name)

            if not node:
                print(f"  ⚠️ Node not found: {old_name}")
                SKIPPED.append((nk_path, f"Node not found: {old_name}"))
                continue

            if nuke.toNode(new_name):
                msg = f"Target name already exists: {new_name}"
                print(f"  ❌ {msg}")
                FAILED.append((nk_path, msg))
                continue

            node.setName(new_name)
            print(f"  ✅ Renamed '{old_name}' → '{new_name}'")
            True

        return changed

    except Exception as e:
        msg = f"rename_nodes failed: {e}"
        print("  ❌", msg)
        FAILED.append((nk_path, msg))
        return False


# ----------------------------------------------------
# PROCESS
# ----------------------------------------------------
def process_nk_file(nk_path, index, total):
    global MODE
    changed = None
    mode_name = MODE_DESCRIPTIONS.get(MODE, "UNKNOWN MODE")

    print("\n======================================================")
    print(f"[PROCESS # {index} of {total}] Starting: {nk_path}")
    print("======================================================")

    print("  ---> Resetting Nuke script state ...")
    nuke.scriptClear()

    if not os.path.exists(nk_path):
        msg = "File not found"
        print("  ❌", msg)
        FAILED.append((nk_path, msg))
        return

    print()
    print("  ---> Loading NK file ...")




    try:
        nuke.scriptOpen(nk_path)
        print("  ✔ File loaded successfully.")

    except Exception as e:
        msg = f"Failed to open NK file: {e}"
        print("  ❌", msg)
        FAILED.append((nk_path, msg))
        return
    
    # START HASH
    before_hash = full_scene_hash()

    print()



    if MODE == 1:
        changed = initial_setup(nk_path) # just open and save - nodes clean up will be loaded automatically

    elif MODE == 2:
        create_render_group(
            nk_path,
            replace_render_group=REPLACE_RENDER_GROUP,
            render_version=RENDER_VERSION
        )

    elif MODE == 3:
        changed=render(nk_path, render_version=RENDER_VERSION)

    elif MODE == 4:
        delete_nodes(nk_path, NODES_TO_DELETE)

    elif MODE == 5:
        reset_rootcx(nk_path)

    elif MODE == 6:
        rename_nodes(nk_path, RENAME_MAP)

    else:
        msg = f"Invalid MODE: {MODE}. Skipping processing."
        print("  ❌", msg)
        SKIPPED.append((nk_path, msg))
        return


    if VERBOSE :
    # PRINT CX DATA
        print("  ---> Print CX DATA ...")
        cxproject = nuke.root()['cxproject'].value()
        cxprojectid = nuke.root()['cxprojectid'].value()
        cxshot = nuke.root()['cxshot'].value()
        cxversion = nuke.root()['cxversion'].value()
        cxhandles = nuke.root()['cxhandles'].value()
        print(f"    cxproject : {cxproject}")
        print(f"    cxprojecid : {cxprojectid}")
        print(f"    cxshot : {cxshot}")
        print(f"    cxversion : {cxversion}")
        print(f"    cxhandles : {cxhandles}")
        print()

    print()

    # END HASH
    after_hash = full_scene_hash()
    
    if changed == None : # IF changed not set , meaning that changes depends on hash
        if before_hash == after_hash :
            print("  ▶ No changes detected/procedure was non-modifying → Skipping backup & save.")
            return
    else : # if changed is set then changes depends on changed var.
        if not changed :
            print("  ▶ No changes detected/procedure was non-modifying → Skipping backup & save.")
            return
 
    
    print("  ▶ Changes detected - Process backup & save.")

    change_tokens = []
    all_dots = nuke.allNodes("Dot")
    for dot in all_dots :
        if dot.name().startswith(_CHANGE_TOKEN_) :
            change_tokens.append(dot)

    if change_tokens :
        for i in change_tokens :
            nuke.delete(i)        


    backup_original(nk_path)

    print()
    print("  ///////////////////////////////////////////////////////////////////")
    print("  --->  👉 💾 Saving NK file ...")

    try:
        nuke.scriptSave(nk_path)
        print(f"  ✅ Saved successfully: {nk_path}")

    except Exception as e:
        msg = f"Failed to save NK file: {e}"
        print("  ❌", msg)
        FAILED.append((nk_path, msg))

    print("  ///////////////////////////////////////////////////////////////////")
    print()


# ----------------------------------------------------
# SUMMARY
# ----------------------------------------------------
def print_summary(total_files_processed):
    num_failed = len(FAILED)
    num_skipped = len(SKIPPED)
    num_success = total_files_processed - (num_failed + num_skipped)

    print("\n====================================")
    print("            SUMMARY")
    print("====================================\n")

    print("📊 OVERALL RESULTS:")
    print(f" - **Total Files Checked:** {total_files_processed}")

    if num_success > 0:
        print(f" - ✅ **Successful:** {num_success}")

    if num_failed > 0:
        print(f" - ❌ **Failed:** {num_failed}")

    if num_skipped > 0:
        print(f" - ⚠️ **Skipped:** {num_skipped}")

    print("\n====================================")
    print("            DETAILS")
    print("====================================\n")

    if FAILED:
        print("❌ FAILED FILES:")
        for f, reason in FAILED:
            print(f" - {f}")
            print(f"      → {reason}")
        print()

    else:
        print("✔ No failures.\n")

    if SKIPPED:
        print("⏭ SKIPPED :")
        for f, reason in SKIPPED:
            print(f" - {f}")
        print()

    else:
        print("✔ No skipped files.\n")

    print("====================================\n")



# ----------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------
def main():
    # Get Mode
    mode_description = MODE_DESCRIPTIONS.get(MODE, "UNKNOWN MODE")
    
    # Clear Screen
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')
    clear_screen()


    # Print intuitive starting message
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(f"MODE: {MODE} ( {mode_description} )")
    extra_msg = "    ❗❗❗  IMPORTANT: THIS IS REPLACE MODE  ❗❗❗"

    match MODE:
        case 2:
            print("----> Create RENDER GROUP ( " , ">>> REPLACE ! <<<" if REPLACE_RENDER_GROUP else "SKIP IF EXIST", " )")
            if REPLACE_RENDER_GROUP :
                print(extra_msg)
        case 3:
            print("----> Render " , "( >>> WILL CREATE NEW RENDER GROUP - REPLACE EXISTING ! <<< )" if REPLACE_RENDER_GROUP else "")
            if REPLACE_RENDER_GROUP :
                print(extra_msg)
        case 4:
            print("Delete nodes : ", NODES_TO_DELETE)
        case 6:
            print()
            print("----> Rename nodes :")
            for old,new in RENAME_MAP.items():
                print(f"       {old} → {new}")

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    nk_files = read_file_list(FILE_LIST)

    if not nk_files:
        print("\n❌ No NK files found. Exiting.\n")
        return

    print("\n=== FILES TO PROCESS ===")
    number_of_files_to_show = MAX_FILE_LIST
    for i,f in enumerate(nk_files):
        if i < number_of_files_to_show: 
            print(" -", f)
        else:
            print(" ...")
            break

    print()
    print("-------------------------------- ")
    total = len(nk_files) 
    print("Total files to process:", total)
    print("-------------------------------- ")
    print()

    answer = input("Continue? (Y/N) : ").strip().lower()
    if answer not in ("", "y"):
        print("❌ Canceled by user.")
        sys.exit(0)

    print("✅ Continuing...\n")

    # PROCESS EACH FILE
    for i, nk in enumerate(nk_files, start=1):
        process_nk_file(nk, i, total)

    print("\n=== ALL DONE ===\n")

    # Pass the total count to the summary function
    print_summary(total)



if __name__ == "__main__":
    main()