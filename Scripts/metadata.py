import sys
import os
import json
from datetime import datetime
import re

# -------------------------
# Paths and setup
# -------------------------

if len(sys.argv) < 2:
    sys.exit(1)

input_md_name = sys.argv[1]  # Filename passed from CLI


base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, ".."))

metadata_dir = os.path.join(root_dir, "Articles-Metadata")
drafts_dir = os.path.join(root_dir, "Drafts")

# Sanity check
if not os.path.isdir(metadata_dir):
    sys.exit(1)

if not os.path.isdir(drafts_dir):
    sys.exit(1)

# Full path to Markdown
input_file = os.path.join(drafts_dir, input_md_name)

if not os.path.exists(input_file):
    sys.exit(1)

# Compute base name safely (allow spaces)
basename_raw = os.path.splitext(input_md_name)[0]

# Safe filename: remove unsafe characters
basename = re.sub(r"[^A-Za-z0-9 _-]", "", basename_raw).strip()



# -------------------------
# Read markdown
# -------------------------

with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

# -------------------------
# Parse special fields
# -------------------------

# Thumbnail
m = re.search(r"<thumbnail:(.*?)\|(.*?)>", text)
thumbnail, thumbnailAltText = (m.group(1), m.group(2)) if m else ("", "")

# Check article type BEFORE removing tag
is_article = "<not-article>" not in text

# Remove tags
text = text.replace("<not-article>", "")
text = re.sub(r"<thumbnail:.*?>", "", text)


# -------------------------
# Load existing metadata numbers
# -------------------------

id_to_html = {}
metadata_files = [f for f in os.listdir(metadata_dir) if f.endswith(".json")]

for filename in metadata_files:
    path = os.path.join(metadata_dir, filename)
    with open(path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        article_id = meta.get("article_number")
        html_file = os.path.splitext(filename)[0] + ".html"
        id_to_html[article_id] = html_file

sorted_ids = sorted(id_to_html.keys())

# -------------------------
# Create metadata file
# -------------------------

metadata_path = os.path.join(metadata_dir, f"{basename}.json")


if not is_article:
    sys.exit(0)

if os.path.exists(metadata_path):
    sys.exit(0)

# Assign next article number
article_number = (sorted_ids[-1] + 1) if sorted_ids else 1

metadata = {
    "article_number": article_number,
    "title": basename,
    "date_created": datetime.now().isoformat(),
    "thumbnail": thumbnail,
    "thumbnailAltText": thumbnailAltText
}

# Write JSON file
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=4)

