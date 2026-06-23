import feedparser
import requests
import os
from collections import defaultdict

# ----------------------------
# CONFIG
# ----------------------------

FEEDS = open("feeds.txt", encoding="utf-8").read().splitlines()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
BLOG_ID = os.environ["BLOG_ID"]
REFRESH_TOKEN = os.environ["BLOGGER_REFRESH_TOKEN"]
CLIENT_ID = os.environ["BLOGGER_CLIENT_ID"]
CLIENT_SECRET = os.environ["BLOGGER_CLIENT_SECRET"]

# ----------------------------
# STEP 1: FETCH NEWS
# ----------------------------

articles = []

for url in FEEDS:
    feed = feedparser.parse(url)

    for e in feed.entries[:10]:
        articles.append({
            "title": e.title,
            "link": e.link
        })

# ----------------------------
# STEP 2: SIMPLE DEDUPE
# ----------------------------

seen = set()
clean = []

for a in articles:
    t = a["title"].lower()
    if t not in seen:
        seen.add(t)
        clean.append(a)

# keep top 20
clean = clean[:20]

# ----------------------------
# STEP 3: BUILD PROMPT (BENGALI NEWS)
# ----------------------------

context = "\n".join([f"- {a['title']}" for a in clean])

prompt = f"""
You are a world-class news editor.

Convert these global headlines into 5 short Bengali news briefs.

Rules:
- Do NOT copy sentences
- Write original Bengali summaries
- Keep neutral tone
- Focus on importance
- Each news: Title + 3-4 lines summary

Headlines:
{context}
"""

# ----------------------------
# STEP 4: CALL GROQ (LLAMA)
# ----------------------------

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "llama-3.1-70b-versatile",
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

res = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers=headers,
    json=data
)

content = res.json()["choices"][0]["message"]["content"]

# ----------------------------
# STEP 5: PRINT RESULT (TEST FIRST)
# ----------------------------

print(content)
