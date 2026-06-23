import feedparser
import requests
import os
import hashlib

# ----------------------------
# SAFE ENV LOADER
# ----------------------------

def get_env(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing environment variable: {name}")
    return value

GROQ_API_KEY = get_env("GROQ_API_KEY")

BLOG_ID = get_env("BLOG_ID")
BLOGGER_REFRESH_TOKEN = get_env("BLOGGER_REFRESH_TOKEN")
BLOGGER_CLIENT_ID = get_env("BLOGGER_CLIENT_ID")
BLOGGER_CLIENT_SECRET = get_env("BLOGGER_CLIENT_SECRET")

# ----------------------------
# RSS SOURCES
# ----------------------------

FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.dw.com/en/top-stories/s-9097/rss",
    "https://www.theguardian.com/world/rss",
    "https://techcrunch.com/feed/",
    "https://www.thedailystar.net/frontpage/rss.xml",
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCN6sm8iHiPd0cnoUardDAnw"
]

# ----------------------------
# FETCH NEWS
# ----------------------------

articles = []

for url in FEEDS:
    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:8]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if title:
                articles.append({"title": title, "link": link})

    except Exception as e:
        print(f"Feed error: {url} -> {e}")

print("Collected:", len(articles))

# ----------------------------
# DEDUPE
# ----------------------------

seen = set()
clean = []

for a in articles:
    key = a["title"].lower().strip()

    if key not in seen:
        seen.add(key)
        clean.append(a)

clean = clean[:25]

print("After dedupe:", len(clean))

# ----------------------------
# BUILD PROMPT
# ----------------------------

headlines = "\n".join([f"- {a['title']}" for a in clean])

prompt = f"""
You are a professional Bangladeshi international news editor.

Select ONLY the 5 most important news items.

Write in fluent Bangla.

Format:

Title:
Summary (3-4 lines)

Rules:
- No copying sentences
- Neutral journalism tone
- Mix Bangladesh + global news

Headlines:
{headlines}
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
    "temperature": 0.6
}

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=60
)

print("GROQ STATUS:", response.status_code)
print("GROQ RAW:", response.text)

if response.status_code != 200:
    raise Exception("Groq API failed")

content = response.json()["choices"][0]["message"]["content"]

# ----------------------------
# BLOGGER TOKEN (SAFE FIXED VERSION)
# ----------------------------

def get_access_token():
    url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": BLOGGER_CLIENT_ID,
        "client_secret": BLOGGER_CLIENT_SECRET,
        "refresh_token": BLOGGER_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    r = requests.post(url, data=data)

    print("TOKEN STATUS:", r.status_code)
    print("TOKEN RAW:", r.text)

    result = r.json()

    if "access_token" not in result:
        raise Exception("OAuth failed. Check refresh token / client ID / secret.")

    return result["access_token"]

# ----------------------------
# BLOGGER POST FUNCTION
# ----------------------------

def post_to_blogger(title, html):
    token = get_access_token()

    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "content": html
    }

    r = requests.post(url, headers=headers, json=payload)

    print("BLOGGER STATUS:", r.status_code)
    print("BLOGGER RAW:", r.text)

# ----------------------------
# HTML FORMAT
# ----------------------------

article_title = "আজকের শীর্ষ বাংলাদেশ ও বিশ্ব সংবাদ"

safe_content = content.replace("\n", "<br>")

article_html = f"""
<div style="font-family: Arial; line-height:1.6;">
    <h2>{article_title}</h2>
    <div>{safe_content}</div>
    <hr>
    <small>AI automated news system</small>
</div>
"""

# ----------------------------
# DUPLICATE PREVENTION
# ----------------------------

post_id = hashlib.md5(article_title.encode()).hexdigest()

try:
    with open("last_post.txt") as f:
        last = f.read()
        if last == post_id:
            print("Duplicate detected. Skipping post.")
            exit()
except:
    pass

with open("last_post.txt", "w") as f:
    f.write(post_id)

# ----------------------------
# FINAL POST
# ----------------------------

post_to_blogger(article_title, article_html)
