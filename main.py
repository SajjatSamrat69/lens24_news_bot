import feedparser
import requests
import os
import hashlib
from collections import defaultdict
from newspaper import Article
from extractor import fetch_news

# ----------------------------
# ENV
# ----------------------------


def extract_article(url):
    try:
        article= Article(url)
        article.download()
        article.parse()

        text = article.text.strip()

        if len(text) < 100:
            return ""

        return text[:5000]
    except Exception as e:
        print("Article Error:", e)
        return ""

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
            "model": "llama-3.3-70b-versatile",
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
    CATEGORIES[k] = CATEGORIES[k][:8]

# ----------------------------
# BUILD FINAL OUTPUT PER CATEGORY
# ----------------------------
def generate_news_block(category, item):
    article_text= item.get("content"," ")

    if len(article_text.strip()) < 100:
        article_text=item.get("summary", " ")

    if len(article_text.strip()) < 50:
        article_text=item["title"]
        
    prompt = f"""
    আপনি বাংলাদেশের একটি শীর্ষস্থানীয় জাতীয় দৈনিক পত্রিকার প্রধান সম্পাদক এবং অনুসন্ধানী সাংবাদিকতার বিশেষজ্ঞ।

    আপনার কাজ হলো প্রদত্ত তথ্যের ভিত্তিতে একটি পূর্ণাঙ্গ, নির্ভুল, তথ্যসমৃদ্ধ ও পেশাদার সংবাদ প্রতিবেদন তৈরি করা।

    সংবাদের বিভাগ:
    {category}

    শিরোনাম:
    {item["title"]}

    মূল তথ্য:
    {article_text}

    লেখার নির্দেশনা:

    * সংবাদটি এমনভাবে লিখতে হবে যেন এটি বাংলাদেশের প্রথম সারির একটি পত্রিকায় প্রকাশিত হচ্ছে।

    * প্রথম অনুচ্ছেদে ঘটনার সবচেয়ে গুরুত্বপূর্ণ তথ্য, স্থান, সংশ্লিষ্ট ব্যক্তি বা প্রতিষ্ঠানের নাম এবং মূল বিষয় তুলে ধরতে হবে।

    * পরবর্তী অনুচ্ছেদগুলোতে ঘটনার পটভূমি, কারণ, প্রেক্ষাপট, সংশ্লিষ্ট পক্ষের ভূমিকা, সম্ভাব্য প্রভাব এবং পাঠকের জন্য গুরুত্বপূর্ণ তথ্য ব্যাখ্যা করতে হবে।

    * প্রদত্ত তথ্য থেকে যৌক্তিকভাবে ব্যাখ্যা করা যাবে, তবে কোনো নতুন তথ্য, সংখ্যা, উদ্ধৃতি, দাবি বা ঘটনা তৈরি করা যাবে না।

    * সংবাদটি ৩০০ থেকে ৫০০ শব্দের মধ্যে লিখতে হবে।

    * কমপক্ষে ৫টি সুসংগঠিত অনুচ্ছেদ থাকতে হবে।

    * প্রতিটি অনুচ্ছেদে একটি নির্দিষ্ট তথ্য বা দিক তুলে ধরতে হবে।

    * ভাষা হবে প্রমিত, সাবলীল, পরিশীলিত এবং সংবাদপত্র-উপযোগী বাংলা।

    * অনুবাদধর্মী, যান্ত্রিক বা কৃত্রিম বাক্য গঠন ব্যবহার করা যাবে না।

    * অপ্রয়োজনীয় ইংরেজি শব্দ ব্যবহার করা যাবে না, তবে ব্যক্তি, প্রতিষ্ঠান বা চলচ্চিত্রের নাম ইংরেজিতে রাখা যাবে।

    * একই তথ্য পুনরাবৃত্তি করা যাবে না।

    * “উল্লেখ্য যে”, “এদিকে”, “অপরদিকে”, “বলা হচ্ছে” ইত্যাদি ক্লিশে বাক্যাংশের অতিরিক্ত ব্যবহার এড়িয়ে চলতে হবে।

    * সংবাদটি পড়ে পাঠক যেন ঘটনার গুরুত্ব, প্রেক্ষাপট এবং সম্ভাব্য প্রভাব সম্পর্কে পরিষ্কার ধারণা পায়।

    * পাঠকের কৌতূহল ধরে রাখার মতো স্বাভাবিক ও পেশাদার সাংবাদিকতামূলক প্রবাহ বজায় রাখতে হবে।

    * কোনো বুলেট পয়েন্ট, নম্বর তালিকা বা উপশিরোনাম ব্যবহার করা যাবে না।

    * কোনো ভূমিকা বা ব্যাখ্যা নয়, শুধুমাত্র চূড়ান্ত সংবাদ প্রতিবেদন লিখুন।

    * সংবাদের শেষ অনুচ্ছেদে ঘটনার সামগ্রিক তাৎপর্য বা সম্ভাব্য প্রভাব সংক্ষেপে তুলে ধরুন।

    অত্যন্ত গুরুত্বপূর্ণ:

    শুধুমাত্র প্রদত্ত তথ্য ব্যবহার করুন। কোনো তথ্য অনুমান, উদ্ভাবন বা কল্পনা করা যাবে না। তথ্য না থাকলে তা পূরণ করার চেষ্টা করবেন না।
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
            "temperature": 0.2
         }
    )

    try:
      data = r.json()
      print(data)   # Debug
      return data["choices"][0]["message"]["content"]

    except Exception as e:
      print("Groq Error:", e)
      print("Response:", r.text)
      return "Nothing found"
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
