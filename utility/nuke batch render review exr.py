import nuke
import sys

RENDER_NODE = "_RENDER_REVIEW_EXR"
ROOT = nuke.root()

def render_review_node(nk_file):
    print("\n==============================")
    print("Processing:", nk_file)
    print("==============================")

    nuke.scriptClear()
    nuke.scriptOpen(nk_file)

    node = nuke.toNode(RENDER_NODE)
    if not node:
        print(f"❌ Node '{RENDER_NODE}' not found. Skipping.")
        return

    # Determine frame range from the Render node itself (preferred)
    handles = ROOT['cxhandles'].value()
    first = 1001 #int(ROOT["first_frame"].value() +handles -1 )
    last  = 1001 #int(ROOT["last_frame"].value() -handles)

    print(f"🎬 Rendering node: {RENDER_NODE}")
    print(f"   Frames: {first} – {last}")

    try:
        nuke.execute(RENDER_NODE, first, last)
        print("✅ Render completed")
    except Exception as e:
        print(f"❌ Render FAILED: {e}")

if __name__ == "__main__":
    nk_files = sys.argv[1:]

    if not nk_files:
        print("Usage:")
        print("  Nuke15.1 --nukex -t render_review_exr.py file1.nk file2.nk ...")
        sys.exit(1)

    for f in nk_files:
        render_review_node(f)

    print("\n🎉 DONE — All renders finished.\n")
