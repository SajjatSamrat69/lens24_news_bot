import feedparser
import requests
import os
from collections import defaultdict

# ----------------------------
# SAFE ENV LOADING (NO KeyError)
# ----------------------------

def get_env(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing required environment variable: {name}")
    return value

GROQ_API_KEY = get_env("GROQ_API_KEY")
BLOG_ID = get_env("BLOG_ID")
REFRESH_TOKEN = get_env("BLOGGER_REFRESH_TOKEN")
CLIENT_ID = get_env("BLOGGER_CLIENT_ID")
CLIENT_SECRET = get_env("BLOGGER_CLIENT_SECRET")

# ----------------------------
# RSS FEEDS
# ----------------------------

with open("feeds.txt", "r", encoding="utf-8") as f:
    FEEDS = [line.strip() for line in f if line.strip()]

# ----------------------------
# STEP 1: FETCH NEWS
# ----------------------------

articles = []

for url in FEEDS:
    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", "")
            })
    except Exception as e:
        print(f"Feed error: {url} -> {e}")

print(f"Collected articles: {len(articles)}")

# ----------------------------
# STEP 2: DEDUPLICATION
# ----------------------------

seen = set()
clean_articles = []

for a in articles:
    title = a["title"].strip().lower()

    if title and title not in seen:
        seen.add(title)
        clean_articles.append(a)

# keep top 20
clean_articles = clean_articles[:20]

print(f"After dedupe: {len(clean_articles)}")

# ----------------------------
# STEP 3: BUILD PROMPT (BENGALI NEWS)
# ----------------------------

context = "\n".join(
    [f"- {a['title']}" for a in clean_articles]
)

prompt = f"""
You are a professional Bengali news editor.

Task:
Create 5 high-quality global news briefs in Bengali.

Rules:
- Do NOT copy sentences
- Use simple Bengali journalism style
- Keep neutral tone
- Focus on important world events
- Each news must include:
  Title + 3-4 line summary

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

payload = {
    "model": "llama-3.1-70b-versatile",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7
}

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers=headers,
    json=payload,
    timeout=60
)

if response.status_code != 200:
    raise Exception(f"Groq API failed: {response.text}")

result = response.json()
content = result["choices"][0]["message"]["content"]

# ----------------------------
# STEP 5: OUTPUT (TEMPORARY)
# ----------------------------

print("\n================ BENGALI NEWS ================\n")
print(content)
print("\n==============================================\n"
