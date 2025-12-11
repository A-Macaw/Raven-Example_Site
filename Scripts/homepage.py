from datetime import datetime
import json
import os
import re
import markdown

# ------------------------------------------------------------
# Locate Root Directory
# ------------------------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
current = base_dir
root_dir = None
while current != os.path.dirname(current):
    if os.path.basename(current) == "Raven":
        root_dir = current
        break
    current = os.path.dirname(current)
if root_dir is None:
    raise FileNotFoundError("Could not find 'Raven' folder in parent directories.")

# ------------------------------------------------------------
# Directory Setup
# ------------------------------------------------------------
drafts_dir = os.path.join(root_dir, "Drafts")
articles_html_dir = os.path.join(root_dir, "Articles-html")
articles_md_dir = os.path.join(root_dir, "Articles-md")
metadata_dir = os.path.join(root_dir, "Articles-Metadata")
site_html_dir = os.path.join(root_dir, "Site-html")
config_dir = os.path.join(root_dir, "Config")

# ------------------------------------------------------------
# Set config vars in case of broken json
# ------------------------------------------------------------
display = 5
previewLength = 150

# Load config
homepage_path = os.path.join(metadata_dir, "homepage.json")
if os.path.exists(homepage_path):
    with open(homepage_path, "r", encoding="utf-8") as f:
        homepage_meta = json.load(f)
    for key, value in homepage_meta.items():
        globals()[key] = value

# ------------------------------------------------------------
# Date formatting
# ------------------------------------------------------------
def getFormattedDate(date_created_iso):
    if not date_created_iso:
        return "Unknown Date"
    try:
        dt = datetime.fromisoformat(date_created_iso)
    except Exception as e:
        print(f"Invalid date format: {e}")
        return "Unknown Date"

    def ordinal(n):
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    return f"{ordinal(dt.day)} {dt.strftime('%B %Y, %H:%M')}"

# ------------------------------------------------------------
# Preview generator
# ------------------------------------------------------------
def make_preview(content: str, previewLength: int) -> str:
    # 1. Remove first H1 heading (robust to extra spaces and line endings)
    content = re.sub(r"(?m)^#\s+.*(?:\r?\n|$)", "", content, count=1)

    # 2. Remove custom tags entirely
    content = re.sub(r"<not-article>", "", content)
    content = re.sub(r"<thumbnail:[^>|]+\|[^>]+>", "", content)

    # 3. Remove markdown images
    content = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", content)

    # 4. Calculate cutoff based on visible characters
    visible_count = 0
    cutoff_index = 0
    length = len(content)

    while cutoff_index < length and visible_count < previewLength:
        # Handle markdown links: only count visible text
        if content[cutoff_index] == "[":
            end_bracket = content.find("]", cutoff_index)
            if end_bracket != -1:
                visible_count += end_bracket - cutoff_index - 1
                cutoff_index = end_bracket + 1
                if cutoff_index < length and content[cutoff_index] == "(":
                    end_paren = content.find(")", cutoff_index)
                    if end_paren != -1:
                        cutoff_index = end_paren + 1
                continue

        visible_count += 1
        cutoff_index += 1

    # 5. Avoid cutting inside a word
    while cutoff_index < length and re.match(r"[A-Za-z0-9]", content[cutoff_index]):
        cutoff_index += 1

    # 6. Ensure code fences are respected (extend if inside ``` block)
    code_fence_starts = [m.start() for m in re.finditer(r"```", content)]
    for start in code_fence_starts:
        if start < cutoff_index:
            end = content.find("```", start + 3)
            if end != -1 and end > cutoff_index:
                cutoff_index = end + 3

    preview = content[:cutoff_index].strip() + "..."
    return preview

# ------------------------------------------------------------
# Globals for article data
# ------------------------------------------------------------
mainlist = []
i = 0

def addPage(input):
    global i
    keys_order = ['article_number', 'title', 'date_created', 'thumbnail', 'thumbnailAltText']

    # Add to mainlist
    for key in keys_order:
        mainlist.append(input.get(key))

    def safe_get(offset):
        index = offset + (i * 5)
        return mainlist[index] if index < len(mainlist) else "default text"

    id = safe_get(0)
    title = safe_get(1)
    dateRaw = safe_get(2)
    date = getFormattedDate(dateRaw)
    thumbnailLoc = safe_get(3)
    thumbnailAltText = safe_get(4)

    thumbnail = f'![{thumbnailAltText}]({thumbnailLoc})'

    md_path = os.path.join(articles_md_dir, f"{title}.md")
    if not os.path.exists(md_path):
        print(f"Markdown file not found: {md_path}")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip first H1 consistently for preview and printing
    content_no_h1 = re.sub(r"(?m)^#\s+.*(?:\r?\n|$)", "", content, count=1)

    preview = make_preview(content_no_h1, previewLength)

    previewProcessed = markdown.markdown(
        preview,
        extensions=['extra','smarty','toc','sane_lists','codehilite','md_in_html'],
        extension_configs={
            'smarty': {'smart_quotes': True, 'smart_dashes': True, 'smart_ellipses': True},
            'codehilite': {'guess_lang': True, 'linenums': True, 'pygments_style': 'monokai', 'noclasses': True}
        },
        output_format="html5"
    )


   

# ------------------------------------------------------------
# Find most recent articles
# ------------------------------------------------------------
def findRecents(display, metadata_dir, addPage):
    global i
    metadata_entries = []
    seen = set()

    for filename in os.listdir(metadata_dir):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(metadata_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            article_num = data.get("article_number")
            if article_num is not None and article_num not in seen:
                seen.add(article_num)
                metadata_entries.append(data)

        except Exception as e:
            print(f"Skipping {filename}: {e}")

    # Sort DESC by article_number
    metadata_entries.sort(key=lambda m: m.get("article_number", -1), reverse=True)

    most_recent = metadata_entries[:display]

    for meta in most_recent:
        addPage(meta)
        i += 1

# ------------------------------------------------------------
# Run
# ------------------------------------------------------------
findRecents(display, metadata_dir, addPage)
