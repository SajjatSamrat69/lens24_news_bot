import feedparser
import requests
import os
import hashlib
from extractor import fetch_news

# ----------------------------
# ENV
# ----------------------------


def env(name):
    v = os.getenv(name)
    if not v:
        raise Exception(f"Missing env: {name}")
    return v

GROQ_API_KEY = env("GROQ_API_KEY")

headers={
    "Authorization":f"Bearer {GROQ_API_KEY}",
    "Content-Type":"application/json"
}


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


items = fetch_news(FEEDS)

print("Fetched:", len(items))

for x in items[:3]:
    print("="*50)
    print("TITLE:", x["title"])
    print("SUMMARY:", x["summary"][:150])
    print("CONTENT LENGTH:", len(x["content"]))


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

clean = clean[:30]

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


# ----------------------------
# DISTRIBUTE
# ----------------------------

for i in clean:

    source = i["source"].lower()
    title = i["title"].lower()

    if "espn" in source:
        cat = "খেলাধুলা"

    elif "techcrunch" in source:
        cat = "বিজ্ঞান ও প্রযুক্তি"

    elif "bbc" in source or "guardian" in source or "al jazeera" in source or "dw" in source:
        cat = "আন্তর্জাতিক"

    elif "the daily star" in source:
        cat = "দেশীয় রাজনীতি"

    else:
        cat = "আন্তর্জাতিক"

    CATEGORIES[cat].append(i)
# limit per category (balance fix)
for k in CATEGORIES:
    CATEGORIES[k] = CATEGORIES[k][:2]

# ----------------------------
# BUILD FINAL OUTPUT PER CATEGORY
# ----------------------------
def generate_news_block(category, item):
   
    article_text = item.get("content", "")

    if len(article_text.strip()) < 100:
        article_text = item.get("summary", "")

    if len(article_text.strip()) < 50:
        article_text = item["title"]

    # ----------------------------
    # CLEAN THE ARTICLE TEXT
    # ----------------------------
    article_text = article_text.replace("\n", " ")
    article_text = " ".join(article_text.split())
    article_text = article_text[:1500]

    prompt = f"""
    আপনি বাংলাদেশের একটি শীর্ষস্থানীয় জাতীয় দৈনিকের জ্যেষ্ঠ সম্পাদক।

    নিচে ইংরেজি ভাষায় একটি সংবাদ বা সংবাদসংক্রান্ত তথ্য দেওয়া হয়েছে।

    আপনার কাজ হলো সেই তথ্যের ভিত্তিতে সম্পূর্ণ নতুনভাবে প্রমিত, স্বাভাবিক ও সংবাদপত্র-উপযোগী বাংলায় একটি সংবাদ লিখা।

    ইংরেজি বাক্য কপি করা যাবে না।

    বাংলায় স্বাভাবিকভাবে অনুবাদ ও পুনর্লিখন করতে হবে।

    শুধুমাত্র প্রদত্ত তথ্য ব্যবহার করবেন।

    কোনো তথ্য উদ্ভাবন করবেন না।

    সংবাদের বিভাগ:
    {category}

    শিরোনাম:
    {item["title"]}

    তথ্য:
    {article_text}

    নির্দেশনা:

    • ১৮০–২৫০ শব্দ
    • ৩–৪ অনুচ্ছেদ
    • পুনরাবৃত্তি নয়
    • শুধুমাত্র বাংলা সংবাদ লিখুন
    """
   
    
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1
         }
    )
    data = r.json()

    if "error" in data:
      print(data["error"]["message"])
      if len(item.get("content", "")) > 200:
        return item["content"]

      elif len(item.get("summary", "")) > 50:
        return item["summary"]

      else:
        return item["title"]

    return data["choices"][0]["message"]["content"]
# ----------------------------
# BUILD HTML
# ----------------------------

final_html = ""

for cat, items in CATEGORIES.items():

    if not items:
        continue


    for i in items:
        block = generate_news_block(cat,i)
        img = i.get("image", "")

        if img:
            final_html += f'<img src="{img}" style="width:100%;max-height:250px;object-fit:cover;">'

        final_html += f"""
        <h3>{i['title']}</h3>

        <p>
        <b>সূত্র:</b> {i['source']}
        </p>

        <div style="font-size:18px;line-height:1.9;margin-top:15px;margin-bottom:20px;">
        {block.replace(chr(10), '<br><br>')}
        </div>

        <p>
        <a href="{i['link']}">মূল সংবাদ</a>
        </p>

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

#final_html = clean_html(final_html)

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
    "শীর্ষ সংবাদ",
    final_html,
    ["বাংলাদেশ", "আন্তর্জাতিক", "খেলাধুলা", "বিনোদন", "প্রযুক্তি"]
)
