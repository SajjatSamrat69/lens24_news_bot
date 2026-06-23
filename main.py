import feedparser
import requests
import os

# ----------------------------
# SAFE ENV LOADER (NO CRASHES)
# ----------------------------

def get_env(name):
    value = os.getenv(name)
    if not value:
        raise Exception(f"Missing environment variable: {name}")
    return value

GROQ_API_KEY = get_env("GROQ_API_KEY")

# Blogger (not used yet, but prepared for next step)
BLOG_ID = get_env("BLOG_ID")
BLOGGER_REFRESH_TOKEN = get_env("BLOGGER_REFRESH_TOKEN")
BLOGGER_CLIENT_ID = get_env("BLOGGER_CLIENT_ID")
BLOGGER_CLIENT_SECRET = get_env("BLOGGER_CLIENT_SECRET")

# ----------------------------
# FEEDS
# ----------------------------

with open("feeds.txt", "r", encoding="utf-8") as f:
    FEEDS = [line.strip() for line in f if line.strip()]

# ----------------------------
# FETCH NEWS
# ----------------------------

articles = []

for url in FEEDS:
    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if title:
                articles.append({
                    "title": title,
                    "link": link
                })

    except Exception as e:
        print(f"Feed error: {url} -> {e}")

print(f"Collected: {len(articles)} articles")

# ----------------------------
# DEDUPLICATION
# ----------------------------

seen = set()
clean = []

for a in articles:
    t = a["title"].lower()

    if t not in seen:
        seen.add(t)
        clean.append(a)

clean = clean[:20]

print(f"After dedupe: {len(clean)}")

# ----------------------------
# BUILD PROMPT (BENGALI NEWS)
# ----------------------------

headlines = "\n".join([f"- {a['title']}" for a in clean])

prompt = f"""
You are a professional Bengali news editor.

Create 5 important world news briefs in Bengali.

Rules:
- Do NOT copy sentences
- Use simple Bengali
- Neutral tone
- Focus on important global events
- Each news item: Title + 3-4 line summary

Headlines:
{headlines}
"""

# ----------------------------
# GROQ CALL (DEBUG ENABLED)
# ----------------------------

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    # SAFE DEFAULT MODEL (change if needed)
    "model": "llama-3.1-8b-instant",
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

# ----------------------------
# FULL DEBUG OUTPUT
# ----------------------------

print("\nSTATUS CODE:", response.status_code)
print("RAW RESPONSE:\n", response.text)

if response.status_code != 200:
    raise Exception("Groq API failed (see error above)")

result = response.json()
content = result["choices"][0]["message"]["content"]

# ----------------------------
# OUTPUT
# ----------------------------

print("\n================ BENGALI NEWS ================\n")
print(content)
print("\n==============================================\n")
