import os
import time
import feedparser
from groq import Groq
from googleapiclient.discovery import build

# --- CORE CONFIGURATION ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_Rqi7My09C786WQVCf8BYWgdyb3FYmpwebe8aTyIYcyE2gOZzbzD")
BLOGGER_API_KEY = os.environ.get("BLOGGER_API_KEY", "AIzaSyCcdlaxhi3mNjF-pfTBsWOVezl9mmRcUm4")
BLOG_ID = os.environ.get("BLOG_ID", "1222511286621075933")

FEEDS = {
    'World News': 'https://google.com',
    'Technology': 'https://google.com',
    'Business': 'https://google.com',
    'Science': 'https://google.com'
}

NICHE_TAGS = {
    'World News': 'আন্তর্জাতিক',
    'Technology': 'প্রযুক্তি',
    'Business': 'ব্যবসায়',
    'Science': 'বিজ্ঞান'
}

HISTORY_FILE = "posted_history.txt"
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("")

groq_client = Groq(api_key=GROQ_API_KEY)
blogger = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(f.read().splitlines())
    except Exception:
        return set()

def save_to_history(url):
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")
    except Exception:
        pass

def run_portal():
    posted_links = load_history()
    print("\n🤖 Scanning global networks...")

    for niche, feed_url in FEEDS.items():
        parsed_feed = feedparser.parse(feed_url)
        bangla_label = NICHE_TAGS.get(niche, 'লাইভ আপডেট')
        
        for entry in parsed_feed.entries[:2]:
            if entry.link in posted_links:
                continue
            
            print(f"🔥 Processing: {entry.title}")
            
            title_prompt = f"Translate this headline into standard journalistic Bangla. Return ONLY the translated string, absolutely no notes or extra text: {entry.title}"
            body_prompt = f"Rewrite this article summary into an engaging news story paragraph in pure Bangla. Structure using plain text, do not add headers or labels. Content: {entry.description}"
            
            try:
                t_comp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.1
                )
                final_title = t_comp.choices.message.content.strip().replace('"', '')

                b_comp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": body_prompt}],
                    temperature=0.5
                )
                final_content = b_comp.choices.message.content.strip()

                post_payload = {
                    "kind": "blogger#post",
                    "title": final_title,
                    "content": f"<p>{final_content}</p>",
                    "labels": [str(bangla_label), "ব্রেকিং নিউজ"]
                }
                
                blogger.posts().insert(blogId=BLOG_ID, body=post_payload).execute()
                print(f"✅ Published successfully to '{bangla_label}' layout section!")
                
                save_to_history(entry.link)
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error during layout integration: {e}")

if __name__ == '__main__':
    while True:
        try:
            run_portal()
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(1800)
