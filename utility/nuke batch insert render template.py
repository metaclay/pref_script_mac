import nuke
import os
import sys

# =============================================================================
# SETTINGS
# =============================================================================

TEMPLATE_FILE = "/Users/andi/Desktop/temp/render_exr.nk"
TEMPLATE_NODE_NAME = "_RENDER_REVIEW_EXR"

REF_NODE_NAME = "REFORMAT_REF"

OFFSET_X = 200     # how far to place the template node to the right

# =============================================================================
# FUNCTIONS
# =============================================================================


def load_template_node():
    """Load the single template node from the template NK script."""
    before = set(nuke.allNodes())
    nuke.nodePaste(TEMPLATE_FILE)
    after = set(nuke.allNodes())

    # Detect the newly created node
    new_nodes = after - before
    if not new_nodes:
        raise RuntimeError("Template paste failed — no new node found!")

    node = list(new_nodes)[0]

    if node.name() != TEMPLATE_NODE_NAME:
        node.setName(TEMPLATE_NODE_NAME, unique=True)

    return node


def add_branch_after(ref_node, tmpl_node, offset_x=200):
    """Make tmpl_node a new branch of ref_node (sibling of existing outputs)."""

    # Connect template node as a new output branch
    tmpl_node.setInput(0, ref_node)

    # Detect existing outputs (dependents)
    deps = ref_node.dependent()  # list of (node, inputindex)
    
    if deps:
        # Find the rightmost existing dependent
        rightmost = max(deps, key=lambda d: d[0].xpos())[0]

        # Place template node to the right of the rightmost dependent
        tmpl_node.setXpos(rightmost.xpos() + offset_x)
        tmpl_node.setYpos(rightmost.ypos())
    else:
        # No existing outputs, place it to the right of the ref node
        tmpl_node.setXpos(ref_node.xpos() + offset_x)
        tmpl_node.setYpos(ref_node.ypos())



def process_file(nk_file):
    print("\n==============================")
    print("Processing:", nk_file)
    print("==============================")

    nuke.scriptClear()
    nuke.scriptOpen(nk_file)

    ref = nuke.toNode(REF_NODE_NAME)
    if not ref:
        print("❌ No REFORMAT_REF node found. Skipping.")
        return

    # Load template node
    tmpl = load_template_node()

    # Add as branch instead of inline
    add_branch_after(ref, tmpl, OFFSET_X)

    # Save script
    nuke.scriptSave(nk_file)
    print("✅ Saved:", nk_file)



# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Files passed from shell
    nk_files = sys.argv[1:]

    if not nk_files:
        print("Usage:")
        print("    Nuke15.1 --nukex -t batch_insert_render_template.py file1.nk file2.nk ...")
        sys.exit(1)

    for path in nk_files:
        process_file(path)

    print("\n🎉 DONE — All scripts processed.\n")
