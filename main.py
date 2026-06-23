import feedparser
import requests
import os
import hashlib

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
# SOURCES
# ----------------------------

FEEDS = [
    # International
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.dw.com/en/top-stories/s-9097/rss",

    # Tech
    "https://techcrunch.com/feed/",

    # Entertainment / Sports
    "https://www.theguardian.com/world/rss",
    "https://feeds.espn.com/espn/rss/news",

    # Bangladesh
    "https://www.thedailystar.net/frontpage/rss.xml",

    # Jamuna TV (YouTube)
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCN6sm8iHiPd0cnoUardDAnw"
]

# ----------------------------
# FETCH
# ----------------------------

items = []

for url in FEEDS:
    try:
        feed = feedparser.parse(url)

        for e in feed.entries[:7]:
            title = e.get("title", "").strip()
            link = e.get("link", "")

            image = ""
            if "media_content" in e:
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
# AI PROMPT (CLASSIFICATION + SUMMARIZATION)
# ----------------------------

context = "\n".join([f"- {x['title']}" for x in clean])

prompt = f"""
You are a professional Bangladeshi newsroom editor.

Classify each news into ONE category:

Categories:
- দেশীয় রাজনীতি
- আন্তর্জাতিক
- খেলাধুলা
- বিনোদন
- বিজ্ঞান ও প্রযুক্তি

Then write a structured news summary in Bengali.

Format for each item:

Category:
Title:
Summary (3-4 lines):
Source Link:

Rules:
- No repetition
- No copying sentences
- Must be factual
- Must match category correctly

Headlines:
{context}
"""

# ----------------------------
# GROQ CALL
# ----------------------------

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.5
}

r = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=60
)

print("GROQ:", r.status_code, r.text)

if r.status_code != 200:
    raise Exception("Groq failed")

content = r.json()["choices"][0]["message"]["content"]

# ----------------------------
# CLEAN TEXT
# ----------------------------

def clean(text):
    return "<br>".join([x.strip() for x in text.split("\n") if x.strip()])

html_body = clean(content)

# ----------------------------
# ACCESS TOKEN
# ----------------------------

def token():
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
# POST BLOGGER
# ----------------------------

def post(title, body, labels):
    t = token()

    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"

    headers = {
        "Authorization": f"Bearer {t}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "content": body,
        "labels": labels
    }

    res = requests.post(url, headers=headers, json=payload)

    print("BLOGGER:", res.status_code, res.text)

# ----------------------------
# CATEGORY DETECTION (simple fallback)
# ----------------------------

def detect_labels(text):
    if "খেলাধুলা" in text:
        return ["খেলাধুলা"]
    if "বিনোদন" in text:
        return ["বিনোদন"]
    if "প্রযুক্তি" in text:
        return ["বিজ্ঞান ও প্রযুক্তি"]
    if "রাজনীতি" in text:
        return ["দেশীয় রাজনীতি"]
    return ["আন্তর্জাতিক"]

labels = detect_labels(content)

# ----------------------------
# DUPLICATE PREVENTION
# ----------------------------

pid = hashlib.md5(content.encode()).hexdigest()

try:
    if open("last.txt").read() == pid:
        print("Duplicate skipped")
        exit()
except:
    pass

open("last.txt", "w").write(pid)

# ----------------------------
# FINAL POST
# ----------------------------

title = "আজকের বাংলাদেশ ও আন্তর্জাতিক সংবাদ"

post(title, html_body, labels)
