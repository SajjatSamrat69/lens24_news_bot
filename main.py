import feedparser
import requests
import os
import hashlib
from collections import defaultdict

# ----------------------------
# ENV
# ----------------------------

def env(name):
    v = os.getenv(name)
    if not v:
        raise Exception(f"Missing env: {name}")
    return v

GROQ_API_KEY = env("GROQ_API_KEY")

BLOG_ID = env("BLOG_ID")
BLOGGER_REFRESH_TOKEN = env("BLOGGER_REFRESH_TOKEN")
BLOGGER_CLIENT_ID = env("BLOGGER_CLIENT_ID")
BLOGGER_CLIENT_SECRET = env("BLOGGER_CLIENT_SECRET")

# ----------------------------
# RSS SOURCES
# ----------------------------

FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.dw.com/en/top-stories/s-9097/rss",
    "https://www.theguardian.com/world/rss",
    "https://feeds.espn.com/espn/rss/news",
    "https://techcrunch.com/feed/",
    "https://www.thedailystar.net/frontpage/rss.xml",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCN6sm8iHiPd0cnoUardDAnw"
]

# ----------------------------
# FETCH
# ----------------------------

items = []

for url in FEEDS:
    try:
        feed = feedparser.parse(url)

        for e in feed.entries[:6]:
            title = e.get("title", "").strip()
            link = e.get("link", "")

            image = ""
            if hasattr(e, "media_content") and e.media_content:
                image = e.media_content[0].get("url", "")

            if title:
                items.append({
                    "title": title,
                    "link": link,
                    "image": image
                })

    except Exception as ex:
        print("Feed error:", url, ex)

print("Fetched:", len(items))

# ----------------------------
# DEDUPE
# ----------------------------

seen = set()
clean = []

for i in items:
    k = i["title"].lower()

    if k not in seen:
        seen.add(k)
        clean.append(i)

clean = clean[:20]

# ----------------------------
# GROQ SETUP
# ----------------------------

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# ----------------------------
# CATEGORY CLASSIFICATION (STRICT)
# ----------------------------

CATEGORIES = {
    "দেশীয় রাজনীতি": [],
    "আন্তর্জাতিক": [],
    "খেলাধুলা": [],
    "বিনোদন": [],
    "বিজ্ঞান ও প্রযুক্তি": []
}

def classify(title):
    prompt = f"""
Classify this news into ONLY ONE category:

- দেশীয় রাজনীতি
- আন্তর্জাতিক
- খেলাধুলা
- বিনোদন
- বিজ্ঞান ও প্রযুক্তি

News: {title}

Return ONLY category name.
"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
    )

    try:
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return "আন্তর্জাতিক"

# ----------------------------
# DISTRIBUTE
# ----------------------------

for i in clean:
    cat = classify(i["title"])

    if cat not in CATEGORIES:
        cat = "আন্তর্জাতিক"

    CATEGORIES[cat].append(i)

# limit per category (balance fix)
for k in CATEGORIES:
    CATEGORIES[k] = CATEGORIES[k][:2]

# ----------------------------
# BUILD FINAL OUTPUT PER CATEGORY
# ----------------------------

def generate_news(title, category):

    prompt = f"""
You are a professional Bengali newspaper editor.

Write a detailed Bengali news article.

Headline:
{title}

Category:
{category}

Rules:
- 150-200 words
- Multiple paragraphs
- Proper Bengali punctuation
- No bullet points
- No repetition
- Professional newspaper tone
"""

    try:

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.4
            }
        )

        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:

        print("Groq error:", e)

        return None

# ----------------------------
# BUILD HTML
# ----------------------------

final_html = ""

for cat, items in CATEGORIES.items():

    if not items:
        continue

    final_html += f"<h2>{cat}</h2>"


    for i in items:
        img = i.get("image", "")

        if img:
            final_html += f'<img src="{img}" style="width:100%;max-height:250px;object-fit:cover;">'

            article = generate_news(
            i["title"],
            cat
            )

final_html += f"""
<h3>{i['title']}</h3>
<p>{article}</p>
<hr>
"""

# ----------------------------
# CLEAN HTML (REMOVE REPETITION)
# ----------------------------

def clean_html(text):
    lines = text.split("\n")
    seen = set()
    out = []

    for l in lines:
        l = l.strip()
        if l and l not in seen:
            seen.add(l)
            out.append(l)

    return "<br>".join(out)

final_html = clean_html(final_html)

# ----------------------------
# AUTH TOKEN
# ----------------------------

def get_token():
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": BLOGGER_CLIENT_ID,
            "client_secret": BLOGGER_CLIENT_SECRET,
            "refresh_token": BLOGGER_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
    )

    data = r.json()

    if "access_token" not in data:
        raise Exception(f"OAuth error: {data}")

    return data["access_token"]

# ----------------------------
# POST
# ----------------------------

def post(title, content, labels):
    token = get_token()

    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"

    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "title": title,
            "content": content,
            "labels": labels
        }
    )

    print("BLOGGER:", r.status_code, r.text)

# ----------------------------
# DUPLICATE CONTROL
# ----------------------------

post_id = hashlib.md5(final_html.encode()).hexdigest()

try:
    if open("last.txt").read() == post_id:
        print("Duplicate skipped")
        exit()
except:
    pass

open("last.txt", "w").write(post_id)

# ----------------------------
# FINAL POST
# ----------------------------

post(
    "আজকের বাংলাদেশ ও আন্তর্জাতিক শীর্ষ সংবাদ",
    final_html,
    ["বাংলাদেশ", "আন্তর্জাতিক", "খেলাধুলা", "বিনোদন", "প্রযুক্তি"]
)
