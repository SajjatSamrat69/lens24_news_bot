import feedparser
import requests
import os

# ----------------------------
# ENV SAFETY
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
# RSS SOURCES (GLOBAL + BANGLADESH)
# ----------------------------

FEEDS = [
    # Global
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.dw.com/en/top-stories/s-9097/rss",
    "https://www.theguardian.com/world/rss",

    # Sports
    "https://feeds.espn.com/espn/rss/news",

    # Tech
    "https://techcrunch.com/feed/",

    # Bangladesh (key addition)
    "https://www.thedailystar.net/frontpage/rss.xml",
    "https://www.thedailystar.net/news/bangladesh/rss.xml",
]

# ----------------------------
# FETCH ARTICLES
# ----------------------------

articles = []

for url in FEEDS:
    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:8]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if title:
                articles.append({
                    "title": title,
                    "link": link
                })

    except Exception as e:
        print(f"Feed error: {url} -> {e}")

print(f"Total collected: {len(articles)}")

# ----------------------------
# BASIC DEDUPE (improved)
# ----------------------------

seen = set()
clean = []

for a in articles:
    key = a["title"].lower().strip()

    if key not in seen:
        seen.add(key)
        clean.append(a)

clean = clean[:25]

print(f"After dedupe: {len(clean)}")

# ----------------------------
# BUILD PROMPT (BANGLA NEWS ENGINE)
# ----------------------------

headlines = "\n".join([f"- {a['title']}" for a in clean])

prompt = f"""
You are a professional Bangladeshi international news editor.

Task:
From the given headlines, select the 5 most important global or Bangladesh-related news.

Write in fluent standard Bangla.

Format EACH news item like this:

Title:
(Strong Bengali headline)

Summary:
(3-4 lines clear factual explanation)

Rules:
- No copying sentences
- No opinions
- Focus on importance
- Include Bangladesh + global mix
- Avoid repetition

Headlines:
{headlines}
"""

# ----------------------------
# GROQ API CALL
# ----------------------------

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.6
}

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=60
)

print("STATUS:", response.status_code)
print("RAW:", response.text)

if response.status_code != 200:
    raise Exception("Groq API failed")

content = response.json()["choices"][0]["message"]["content"]

# ----------------------------
# BLOGGER READY HTML FORMAT
# ----------------------------

article_title = "আজকের শীর্ষ বাংলাদেশ ও বিশ্ব সংবাদ"

safe_content = content.replace("\n", "<br>")

article_html = f"""
<div style="font-family: Arial; line-height:1.6;">
    <h2>{article_title}</h2>
    <div>{safe_content}</div>
    <hr>
    <small>AI-generated news engine</small>
</div>
"""

# ----------------------------
# OUTPUT
# ----------------------------

print("\n================ FINAL ARTICLE ================\n")
print(article_html)
print("\n==============================================\n")
