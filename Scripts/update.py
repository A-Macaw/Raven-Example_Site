import os
import shutil
import markdown
import json
import re
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# Locate Root Directory ("Raven")
# -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# Directory Setup
# -------------------------------------------------------------------
drafts_dir = os.path.join(root_dir, "Drafts")
articles_html_dir = os.path.join(root_dir, "Articles-html")
articles_md_dir = os.path.join(root_dir, "Articles-md")
metadata_dir = os.path.join(root_dir, "Articles-Metadata")
site_html_dir = os.path.join(root_dir, "Site-html")
config_dir = os.path.join(root_dir, "Config")

config_css_path = os.path.join(config_dir, "global.css")
name_txt_path = os.path.join(config_dir, "name.txt")
toplinks_txt_path = os.path.join(config_dir, "toplinks.txt")
copyright_txt_path = os.path.join(config_dir, "copyright.txt")
topstyle_path = os.path.join(config_dir, "topstyle.css")
bottomstyle_path = os.path.join(config_dir, "bottomstyle.css")
logo_path_full = os.path.join(root_dir, "Images/logo.png")

server_script = os.path.join(root_dir, "Scripts", "server.py")
feeds_script = os.path.join(root_dir, "Scripts", "feeds.py")

# -------------------------------------------------------------------
# Clean old generated articles
# -------------------------------------------------------------------
for d in [articles_html_dir, articles_md_dir]:
    if os.path.exists(d):
        for filename in os.listdir(d):
            file_path = os.path.join(d, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    else:
        os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------------
# Load Style Vars
# -------------------------------------------------------------------
def load_style_vars(path):
    style_vars = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'(\w+)\s+"([^"]*)"', line)
                if match:
                    style_vars[match.group(1)] = match.group(2)
    return style_vars

top_vars = load_style_vars(topstyle_path)
bottom_vars = load_style_vars(bottomstyle_path)

TOP_DIV_STYLE = top_vars.get("TOP_DIV_STYLE", "display:flex; align-items:center; justify-content:space-between; padding:10px 0;")
TOP_LOGO_STYLE = top_vars.get("TOP_LOGO_STYLE", "max-height:60px; margin-right:15px;")
TOP_LINK_STYLE = top_vars.get("TOP_LINK_STYLE", "margin-left:15px; font-size:1.5em")
TOP_H1_STYLE = top_vars.get("TOP_H1_STYLE", "margin:0; font-size:3em; font-style: normal;")
TOP_HR_STYLE = top_vars.get("TOP_HR_STYLE", "border:none; height:1px; background-color:#ccc; margin: 15px 0;")

BOTTOM_HR_STYLE = bottom_vars.get("BOTTOM_HR_STYLE", "border:none; height:1px; background-color:#ccc;")
BOTTOM_DIV_STYLE = bottom_vars.get("BOTTOM_DIV_STYLE", "font-size:1.33em; display:flex; justify-content:space-between; padding:10px 0;")
BOTTOM_COPYRIGHT_STYLE = bottom_vars.get("BOTTOM_COPYRIGHT_STYLE", "text-align:center; font-size:0.9em; margin-top:10px;")

# -------------------------------------------------------------------
# Ensure favicon + Images
# -------------------------------------------------------------------
favicon_target = os.path.join(articles_html_dir, "favicon.ico")
favicon_source = os.path.join(config_dir, "favicon.ico")
if os.path.exists(favicon_target):
    try:
        os.remove(favicon_target)
    except:
        pass
try:
    shutil.copy2(favicon_source, favicon_target)
except:
    pass

images_src = os.path.join(root_dir, "Images")
images_dst = os.path.join(articles_html_dir, "Images")
if os.path.exists(images_dst):
    shutil.rmtree(images_dst)
shutil.copytree(images_src, images_dst)

# Create output dirs
for d in [articles_html_dir, articles_md_dir, metadata_dir, site_html_dir]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------------
# Copy robots.txt if it exists
# -------------------------------------------------------------------
robots_src = os.path.join(config_dir, "robots.txt")
robots_dst = os.path.join(articles_html_dir, "robots.txt")
if os.path.exists(robots_src):
    try:
        shutil.copy2(robots_src, robots_dst)
        print("Copied robots.txt to Articles-html")
    except Exception as e:
        print(f"Failed to copy robots.txt: {e}")



# -------------------------------------------------------------------
# Load Config Data
# -------------------------------------------------------------------
site_name = ""
if os.path.exists(name_txt_path):
    with open(name_txt_path, 'r', encoding='utf-8') as f:
        site_name = f.read().strip()

top_links = []
if os.path.exists(toplinks_txt_path):
    with open(toplinks_txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    top_links.append(parts)

copyright_text = ""
if os.path.exists(copyright_txt_path):
    with open(copyright_txt_path, 'r', encoding='utf-8') as f:
        copyright_text = f.read().strip()

# -------------------------------------------------------------------
# Map article IDs to HTML
# -------------------------------------------------------------------
id_to_html = {}
metadata_files = sorted([f for f in os.listdir(metadata_dir) if f.endswith(".json")])
for filename in metadata_files:
    path = os.path.join(metadata_dir, filename)
    with open(path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
        article_id = int(meta.get("article_number"))
        html_file = os.path.splitext(filename)[0] + ".html"
        id_to_html[article_id] = html_file

sorted_ids = sorted(id_to_html.keys())

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def remove_first_h1(md_text):
    pattern = r'^(#\s+.+)$'
    match = re.search(pattern, md_text, re.MULTILINE)
    if match:
        return md_text.replace(match.group(1), '', 1).lstrip('\n'), match.group(1)[2:].strip()
    else:
        return md_text, ""

def has_meaningful_content(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all():
        if not tag.get_text(strip=True) and tag.name not in ['img', 'math']:
            tag.decompose()
    return bool(soup.get_text(strip=True) or soup.find(['img', 'math']))

def prepend_image_path(match):
    alt_text = match.group(1)
    img_file = match.group(2)
    if '/' not in img_file and '\\' not in img_file:
        img_file = f"../Images/{img_file}"
    return f"![{alt_text}]({img_file})"

def rewrite_html_links(match):
    text_l = match.group(1)
    url = match.group(2)
    if url.endswith(".html"):
        url = "/" + url[:-5]
    return f"[{text_l}]({url})"

def load_fstring_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

# -------------------------------------------------------------------
# Process Draft Markdown Files
# -------------------------------------------------------------------
draft_files = [f for f in os.listdir(drafts_dir) if f.endswith(".md")]

for md_name in draft_files:
    input_file = os.path.join(drafts_dir, md_name)
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    is_article = "<not-article>" not in text
    text = text.replace("<not-article>", "")
    text = re.sub(r"<thumbnail:.*?>", "", text)

    # Remove first H1
    text, first_h1 = remove_first_h1(text)

    # Fix image paths
    text_for_html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', prepend_image_path, text)

    # Rewrite links
    text_for_html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', rewrite_html_links, text_for_html)

    # Convert Markdown → HTML
    html_body = markdown.markdown(
        text_for_html,
        extensions=['extra','smarty','toc','sane_lists','codehilite','md_in_html'],
        extension_configs={
            'smarty': {'smart_quotes': True, 'smart_dashes': True, 'smart_ellipses': True},
            'codehilite': {'guess_lang': True, 'linenums': True, 'pygments_style': 'monokai', 'noclasses': True}
        },
        output_format="html5"
    )

    # -------------------------------------------------------------------
    # Precompute template variables
    # -------------------------------------------------------------------
    article_h1_html = f'<h1 style="{TOP_H1_STYLE}">{first_h1}</h1>' if first_h1 else ""
    article_date_html = ""
    basename = os.path.splitext(md_name)[0]
    metadata_path = os.path.join(metadata_dir, basename + ".json")

    article_id = None
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            article_id = int(meta.get("article_number"))  # <-- FIX: ensure int
            date_created_iso = meta.get("date_created")
            if date_created_iso:
                dt = datetime.fromisoformat(date_created_iso)
                formatted_date = dt.strftime("%d %B %Y, %H:%M")
                article_date_html = f'<div style="font-size:0.9em; margin-bottom: 10px;">{formatted_date}</div>'

    # Relative logo path
    rel_logo_path = os.path.relpath(logo_path_full, articles_html_dir).replace("\\", "/")

    # Top links HTML
    link_fstring = load_fstring_template(os.path.join(config_dir, "toplinksStyle.txt"))
    top_links_html = " ".join([eval(link_fstring) for name, link in top_links])

    # -------------------------------------------------------------------
    # Previous / Next links
    # -------------------------------------------------------------------
    prev_link_html = ""
    next_link_html = ""
    if article_id in sorted_ids:
        idx = sorted_ids.index(article_id)
        if idx > 0:
            prev_file = id_to_html[sorted_ids[idx - 1]]
            prev_link_html = f'<a href="/{prev_file[:-5]}">Previous</a>'
        if idx < len(sorted_ids) - 1:
            next_file = id_to_html[sorted_ids[idx + 1]]
            next_link_html = f'<a href="/{next_file[:-5]}">Next</a>'

    # -------------------------------------------------------------------
    # Separator HTML
    # -------------------------------------------------------------------
    separatorStyle = load_fstring_template(os.path.join(config_dir, "separatorStyle.txt"))
    separator_html = eval(separatorStyle) if has_meaningful_content(html_body) else ""

    # -------------------------------------------------------------------
    # Load page templates
    # -------------------------------------------------------------------
    page_top_fstring = load_fstring_template(os.path.join(config_dir, "page_top.txt"))
    page_top = eval(f"f'''{page_top_fstring}'''")

    page_bottom_fstring = load_fstring_template(os.path.join(config_dir, "page_bottom.txt"))
    page_bottom = eval(f"f'''{page_bottom_fstring}'''")

    page_title     = first_h1 if first_h1 else site_name
    local_css_name = "global.css"
    page_full_fstring = load_fstring_template(os.path.join(config_dir, "page_full.txt"))
    html_full = eval(f"f'''{page_full_fstring}'''")

    # -------------------------------------------------------------------
    # Copy CSS
    # -------------------------------------------------------------------
    local_css_path = os.path.join(articles_html_dir, local_css_name)
    shutil.copy2(config_css_path, local_css_path)

    # -------------------------------------------------------------------
    # Write HTML and Markdown
    # -------------------------------------------------------------------
    html_path = os.path.join(articles_html_dir, basename + '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_full)

    shutil.copy2(input_file, os.path.join(articles_md_dir, md_name))

    # Debug / confirmation
    print(f"Article: {basename}, Prev: {prev_link_html}, Next: {next_link_html}")


source_404 = os.path.join(articles_html_dir, "404.html")

if os.path.isfile(source_404):
    print("404.html found in Articles-html.")

    # --- 2. Copy to Articles-md ---
    dest_404 = os.path.join(articles_md_dir, "404.html")

    # Ensure destination directory exists
    os.makedirs(articles_md_dir, exist_ok=True)

    shutil.copy2(source_404, dest_404)
    print(f"Copied 404.html to: {dest_404}")

else:
    print("404.html NOT found in Articles-html.")

# -------------------------------------------------------------------
# Run feeds and server
# -------------------------------------------------------------------
try:
    subprocess.run(["python3", feeds_script], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error running feed generator: {e}")
