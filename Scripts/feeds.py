import os
import json

#Find Base Dir
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

#Find other folders
articles_md_dir = os.path.join(root_dir, "Articles-md")
articles_html_dir = os.path.join(root_dir, "Articles-html")
metadata_dir = os.path.join(root_dir, "Articles-Metadata")
config_dir = os.path.join(root_dir, "Config")

#Delete old feeds
rss_path = os.path.join(articles_html_dir, "rss.xml")
atom_path = os.path.join(articles_html_dir, "atom.xml")

for feed_file in [rss_path, atom_path]:
    if os.path.exists(feed_file):
        os.remove(feed_file)
        
#Find feeds.json
config = os.path.join(config_dir, "feeds.json")

#Create Variables
siteURL = ""
siteName = ""
rss = ""
atom = ""
i = 0
feedType = ""

#Set Variables
with open(config, "r") as f:
    feed_data = json.load(f)

for key, value in feed_data.items():
    globals()[key] = value

if rss == 1:
    feedType = "rss "
if atom == 1:
    if feedType == "rss ":
        feedType = "rss & atom "
    else:
        feedType = "atom "

if feedType == "rss & atom ":
    feedType = feedType + "feeds"
else:
    feedType = feedType + "feed"

from feedgen.feed import FeedGenerator
fg = FeedGenerator()
fg.id('https://' + siteURL + "/feed")
fg.title(siteName + 'Feed')
fg.author({'name':siteName})
fg.link(href='https://' + siteURL, rel='alternate')
fg.logo('http://' + siteURL + "/Images/logo.png")
fg.language('en')
fg.description(siteName + " " + feedType)

def addFeed(file):
    global i
    fe = fg.add_entry()
    fe.id('https://' + siteURL + "/feed" + "/" + str(i))
    fe.title(file)
    fe.link(href="https://" + siteURL + "/" + file + ".html")
    i += 1

# ---------------------------------------------------------
# NEW SECTION: load metadata, filter, and sort by article_number
# ---------------------------------------------------------

articles = []  # (article_number, article_slug)

for filename in os.listdir(metadata_dir):
    if not filename.endswith(".json"):
        continue

    meta_path = os.path.join(metadata_dir, filename)

    with open(meta_path, "r", encoding="utf-8") as m:
        data = json.load(m)

    # Skip non-article metadata
    if data.get("not-article") is True:
        continue

    article_number = data.get("article_number")
    if article_number is None:
        continue

    article_slug = os.path.splitext(filename)[0]  # corresponds to markdown/html filename

    # Verify article exists in markdown
    md_path = os.path.join(articles_md_dir, article_slug + ".md")
    if not os.path.exists(md_path):
        continue

    articles.append((article_number, article_slug))

# Sort newest first
articles.sort(key=lambda x: x[0], reverse=True)

# Add to feed in order
for _, slug in articles:
    addFeed(slug)

# ---------------------------------------------------------

if rss == 1:
    fg.rss_file(articles_html_dir + '/rss.xml')
if atom == 1:
    fg.atom_file(articles_html_dir + '/atom.xml')
