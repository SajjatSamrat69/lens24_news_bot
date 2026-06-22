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

THUMBNAILS = {
    'World News': 'https://unsplash.com',
    'Technology': 'https://unsplash.com',
    'Business': 'https://unsplash.com',
    'Science': 'https://unsplash.com'
}

# HARDENED: Lives entirely in cloud RAM memory so Render never blocks file creation
POSTED_HISTORY_MEMORY = set()

groq_client = Groq(api_key=GROQ_API_KEY)
blogger = build('blogger', 'v3', developerKey=BLOGGER_API_KEY)

app = Flask(__name__)

@app.route('/')
def home():
    return "News Bot is Live and Running 24/7!"

def run_portal():
    global POSTED_HISTORY_MEMORY
    print("\n🤖 [Lens24 Engine] actively scanning global news networks...")

    for niche, feed_url in FEEDS.items():
        print(f"🔍 Checking channel: {niche}...")
        parsed_feed = feedparser.parse(feed_url)
        bangla_label = NICHE_TAGS.get(niche, 'লাইভ আপডেট')
        img_url = THUMBNAILS.get(niche, 'https://unsplash.com')
        
        # Pulls the single freshest breaking item per loop run to stay safe
        for entry in parsed_feed.entries[:1]:
            if entry.link in POSTED_HISTORY_MEMORY:
                print(f"⏭️ Already processed: {entry.title}")
                continue 
            
            print(f"🔥 Processing breaking story via Groq: {entry.title}")
            
            title_prompt = f"Translate this news headline into professional journalism style Bangla. Return ONLY the translated text, nothing else: {entry.title}"
            body_prompt = (
                f"You are a professional Bangladeshi news reporter. Translate and rewrite the following news article text "
                f"into a high-quality, engaging news post in the Bangla language. Use clean HTML paragraphs (<p>) "
                f"to structure the text formatting cleanly. Do not write a headline. Do not include any English characters.\n\n"
                f"Text to rewrite: {entry.description}"
            )
            
            try:
                # 1. Fetch Bangla title
                t_comp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": title_prompt}],
                    temperature=0.1
                )
                final_title = t_comp.choices.message.content.strip().replace('"', '')

                # 2. Fetch Bangla description
                b_comp = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": body_prompt}],
                    temperature=0.5
                )
                final_content = b_comp.choices.message.content.strip()

                # Embed clean image layout cards straight into the HTML code block stream
                html_content = f'<div class="separator" style="clear: both; text-align: center;"><img src="{img_url}" style="max-width: 100%; height: auto; margin-bottom: 15px;"/></div><p>{final_content}</p>'

                post_payload = {
                    "kind": "blogger#post",
                    "title": final_title,
                    "content": html_content,
                    "labels": [str(bangla_label), "ব্রেকিং নিউজ"]
                }
                
                # Execute direct API injection into your Blogger database layout
                blogger.posts().insert(blogId=BLOG_ID, body=post_payload).execute()
                print(f"✅ Successfully published to '{bangla_label}' site section layout!")
                
                POSTED_HISTORY_MEMORY.add(entry.link)
                time.sleep(5)
                
            except Exception as post_err:
                print(f"❌ Pipeline skip on target item: {post_err}")

def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # 1. Run web server thread to satisfy Render's port checker
    server_thread = threading.Thread(target=start_web_server)
    server_thread.daemon = True
    server_thread.start()
    print("🌐 Internal web port configuration loaded successfully.")
    
    # 2. Run continuous script loops 24/7
    while True:
        try:
            run_portal()
        except Exception as e:
            print(f"Loop error: {e}")
        print("\n⏳ Global scan complete. Sleeping for 30 minutes before next run...")
        time.sleep(1800)
