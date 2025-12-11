import os
import sys
import shutil
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, ".."))

unpublished_dir = os.path.join(root_dir, "Unpublished")
drafts_dir = os.path.join(root_dir, "Drafts")
scripts_dir = os.path.join(root_dir, "Scripts")

if len(sys.argv) != 2:
    sys.exit(1)

md_file = sys.argv[1]

src = os.path.join(unpublished_dir, md_file)
dest = os.path.join(drafts_dir, md_file)

if not os.path.exists(src):
    print(f"Source file not found: {src}")
    sys.exit(1)

# Move markdown file to Drafts
shutil.move(src, dest)

# Run update.py
update_script = os.path.join(scripts_dir, "update.py")
subprocess.run(["python3", update_script], check=True, cwd=scripts_dir)

# Run metadata.py with the markdown filename
metadata_script = os.path.join(scripts_dir, "metadata.py")
subprocess.run(["python3", metadata_script, md_file], check=True, cwd=scripts_dir)
