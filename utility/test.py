


import nuke
import hashlib
import os

FILE_LIST = os.path.expanduser("~/Documents/preferences/script/utility/_file_list2.txt")

def dump_nodes_state():
    state = {}
    for n in nuke.allNodes(recurseGroups=True):
        knobs = {}
        for k in n.knobs():
            try:
                knobs[k] = n[k].value() if hasattr(n[k], 'value') else str(n[k])
            except:
                pass
        state[n.name()] = knobs
    return state


def stable_scene_hash():
    h = hashlib.md5()

    for n in nuke.allNodes(recurseGroups=True):
        h.update(n.Class().encode())
        h.update(n.name().encode())

        # Serialize only knobs that matter (exclude UI junk)
        for k in n.knobs():
            # Skip UI/non-deterministic knobs
            if k in ("xpos", "ypos", "selected", "global_script"):
                continue

            try:
                value = n.knob(k).toScript()
                h.update(value.encode())
            except:
                pass  # Some knobs cannot be serialized cleanly

    return h.hexdigest()


def get_script_hash():
    return stable_scene_hash()


def process_file(nk_path):
    # Read original
    with open(nk_path, 'r') as f:
        raw_before = f.read()

    # Load without script clear? No — clear first
    nuke.scriptClear()
    nuke.scriptOpen(nk_path)

    # Snapshot BEFORE
    before = dump_nodes_state()

    # Load again so onScriptLoad() executes
    # (your callback triggers only on real scriptOpen)
    nuke.scriptClear()
    nuke.scriptOpen(nk_path)

    # Snapshot AFTER
    after = dump_nodes_state()

    if before != after:
        print("\n====== REAL MODIFICATIONS DETECTED ======")

        for node in after:
            if node not in before:
                print(f"Node ADDED: {node}")

        for node in before:
            if node not in after:
                print(f"Node REMOVED: {node}")

        for node in before:
            if node in after:
                # Compare knob by knob
                for k in before[node]:
                    if k not in after[node]:
                        print(f"{node}: knob REMOVED {k}")
                        continue
                    if before[node][k] != after[node][k]:
                        print(f"{node} -> knob '{k}' changed:")
                        print(f"    BEFORE: {before[node][k]}")
                        print(f"    AFTER : {after[node][k]}")
                        print("")
                # new knobs that were added
                for k in after[node]:
                    if k not in before[node]:
                        print(f"{node}: knob ADDED {k} = {after[node][k]}")

        nuke.scriptSave(nk_path)
        print("Saved:", nk_path)

    else:
        print("NO modification detected -> NOT saved")


# ---------- MAIN ----------
with open(FILE_LIST, 'r') as f:
    files = [line.strip() for line in f if line.strip()]

for nk in files:
    process_file(nk)
