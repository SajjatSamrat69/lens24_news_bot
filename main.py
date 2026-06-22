import os
import time
import threading
import feedparser
from flask import Flask
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

# Initialize Production-Grade Groq and Blogger Core Engines
groq_client = Groq(api_key=GROQ_API_KEY)
blogger = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)

# Create a tiny web server to keep Render's port detector happy
app = Flask(_name_)

@app.route('/')
def home():
    return "News Bot is Live and Running 24/7!"

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
    print("\n🤖 [Lens24 Engine] actively scanning global news networks...")

    for niche, feed_url in FEEDS.items():
        print(f"🔍 Checking channel: {niche}...")
        parsed_feed = feedparser.parse(feed_url)
        bangla_label = NICHE_TAGS.get(niche, 'লাইভ আপডেট')
        
        # Pulls the top 2 freshest breaking news posts per channel loop
        for entry in parsed_feed.entries[:2]:
            if entry.link in posted_links:
                continue # Deduplication anchor! Filters out old posts.
            
            print(f"🔥 Processing breaking story via Groq: {entry.title}")
            
            title_prompt = f"Translate this news headline into professional journalism style Bangla. Return ONLY the translated text, nothing else: {entry.title}"
            body_prompt = (
                f"You are a professional Bangladeshi news reporter. Translate and rewrite the following news article text "
                f"into a high-quality, engaging news post in the Bangla language. Use clean HTML paragraphs (<p>) "
                f"to structure the text formatting cleanly. Do not write a headline. Do not include any English characters.\n\n"
                f"Text to rewrite: {entry.description}"
            )
            
            try:
                # 1. Fetch clean Bangla title
                t_comp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.1
                )
                final_title = t_comp.choices.message.content.strip().replace('"', '')

                # 2. Fetch clean HTML structured Bangla content block
                b_comp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": body_prompt}],
                    temperature=0.5
                )
                final_content = b_comp.choices.message.content.strip()

                # Payload build explicitly matching your theme properties
                post_payload = {
                    "kind": "blogger#post",
                    "title": final_title,
                    "content": f"<p>{final_content}</p>",
                    "labels": [str(bangla_label), "ব্রেকিং নিউজ"]
                }
                
                # Direct API push execution bypassing all web layout walls
                blogger.posts().insert(blogId=BLOG_ID, body=post_payload).execute()
                print(f"✅ Successfully published to '{bangla_label}' site section layout!")
                
                save_to_history(entry.link)
                time.sleep(5) # Safe cooldown pipeline spacing buffer
                
            except Exception as post_err:
                print(f"❌ Pipeline skip on target item: {post_err}")

def start_web_server():
    # Render automatically gives us a port via the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # 1. Start the web server in a separate background thread to pass Port check
    server_thread = threading.Thread(target=start_web_server)
    server_thread.daemon = True
    server_thread.start()
    print("🌐 Internal web port configuration loaded successfully.")
    
    # 2. Instantly kick off your main 24/7 news loop right next to it
    while True:
        try:
            run_portal()
        except Exception as e:
            print(f"Loop error: {e}")
        print("\n⏳ Global scan complete. Sleeping for 30 minutes before next run...")
        time.sleep(1800) # Runs completely free 24/7 on a continuous loop
